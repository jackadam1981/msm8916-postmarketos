#!/usr/bin/env python3
"""Audit a vendor device tree against ours, node by node.

The vendor tree from the Android firmware has 873 nodes; ours has 448.  A
naive path diff is useless because the two trees are shaped completely
differently - the vendor one is a downstream 3.10 tree, ours follows the
upstream layout.  compatible strings do not match either (qcom,gcc-8916
vs qcom,gcc-msm8916), so they cannot be the join key.

What does survive both trees is the hardware address in the node name:
usb@78d9000 is the same controller no matter which tree describes it.  This
tool therefore:

  1. buckets every vendor node into a subsystem (USB, storage, network, ...)
     so 873 nodes become a handful of readable groups
  2. joins nodes on @address to compare properties where both trees have
     the same hardware
  3. lists vendor-only nodes per subsystem - those are the candidates for
     "we are missing something", though many are downstream-only (coresight,
     camera, adsp loader) and correctly absent from our tree

Usage:
    dtb_audit.py VENDOR.dtb OURS.dtb [-o report.md] [--domain USB]

Exit code is always 0 - this is a report, not a gate.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import dtb_dump  # noqa: E402
from dtb2dts import render_value  # noqa: E402

# Subsystem buckets, checked in order against "node-name compatible...".
# First match wins, so put the specific ones first: "usb-phy" must land in
# USB, not in the generic PHY bucket.
DOMAINS: list[tuple[str, tuple[str, ...]]] = [
    ("USB", ("usb", "hsusb", "dwc3", "ci-hdrc", "ulpi", "otg", "extcon",
             "usb-phy", "qcom,usb")),
    ("SIM/Modem", ("mpss", "mss-pil", "q6v5", "modem", "mba", "smd", "smem",
                   "smdtty", "sim", "rmnet", "ipcrouter", "glink", "smp2p")),
    ("网络", ("wcnss", "wlan", "wifi", "pronto", "bluetooth", "bam-dmux",
              "netdev", "ethernet")),
    ("存储", ("sdhci", "sdcc", "mmc", "emmc", "sd-card")),
    ("显示", ("mdss", "dsi", "panel", "mdp", "backlight", "framebuffer",
              "spi-panel", "st7735")),
    ("音频", ("lpass", "codec", "sound", "apr", "pcm", "wcd", "micbias",
              "cdc", "audio", "dai", "slim")),
    ("电源/PMIC", ("regulator", "pmic", "rpm", "charger", "chgr", "battery",
                   "vadc", "adc", "thermal", "tsens", "temp-alarm", "power-on",
                   "pon", "resin", "mpp", "spmi", "coincell", "vm-bms",
                   "cpr", "bcl", "gdsc", "power-domain")),
    ("时钟/复位", ("gcc", "clock", "rpmcc", "clk", "reset", "pll")),
    ("IOMMU/中断", ("iommu", "gic", "intc", "interrupt-controller", "msi")),
    ("GPIO/按键/LED", ("pinctrl", "tlmm", "gpio-keys", "key", "led",
                       "gpio-leds", "button")),
    ("串口", ("uart", "blsp", "serial", "hsuart")),
    ("I2C/SPI", ("i2c", "spi", "qup")),
    ("GPU/视频", ("adreno", "gpu", "venus", "vidc", "kgsl", "opp-table")),
    ("摄像头", ("camss", "csid", "csiphy", "cci", "actuator", "eeprom",
                "flash", "isp", "cpp")),
    ("调试/追踪", ("coresight", "etm", "funnel", "replicator", "jtag",
                   "debug", "stm", "tpiu", "fuse", "qseecom")),
    ("CPU/拓扑", ("cpu", "idle-state", "psci", "timer", "pmu", "l2-cache",
                  "cortex", "arm,armv8", "smp")),
    ("内存/保留区", ("memory", "reserved-memory", "ramoops", "memshare",
                     "heap", "dma-pool")),
]

# Properties that are noise in a cross-tree comparison: phandles are allocated
# in tree order so they never match, and cell counts are structural.
IGNORED_PROPS = {
    "phandle", "linux,phandle", "#address-cells", "#size-cells",
    "#interrupt-cells", "#clock-cells", "#gpio-cells", "#phy-cells",
    "#pwm-cells", "#dma-cells", "#sound-dai-cells", "#iommu-cells",
    "#power-domain-cells", "#reset-cells", "#mbox-cells",
    "#thermal-sensor-cells", "#cooling-cells",
    "cell-index", "interrupt-parent", "clocks", "clock-names",
    "clock-frequency", "qcom,clk-rates", "qcom,src-freq",
    "assigned-clocks", "assigned-clock-rates", "assigned-clock-parents",
}

# Properties whose value is a bare phandle (or a list of them).  The number
# differs between trees by construction, so only the presence is meaningful:
# a missing supply is a real difference, a different phandle number is not.
PHANDLE_PROPS = {
    "next-level-cache", "power-domains", "power-domain-names", "memory-region",
    "iommus", "resets", "reset-names", "mboxes", "mbox-names",
    "qcom,acc", "qcom,saw", "qcom,smem-states", "qcom,smem-state-names",
    "nvmem-cells", "nvmem-cell-names", "interconnects", "interconnect-names",
}

PHANDLE_SUFFIXES = ("-supply", "-parent", "-phandle")

# Properties worth surfacing first in a per-node summary.
#
# compatible is deliberately absent: the two trees name the same hardware
# differently (qcom,hsusb-otg vs qcom,ci-hdrc) because one is a 3.10
# downstream tree and the other mainline.  Every single node would light up
# and the real findings would drown.  What matters is whether a device is
# enabled and how it is wired.
KEY_PROPS = (
    "status", "dr_mode", "bus-width", "max-frequency", "maximum-speed",
    "non-removable", "no-1-8-v", "broken-cd", "cd-gpios", "wp-gpios",
    "vmmc-supply", "vqmmc-supply", "phy-names", "role-switch-default-mode",
)


def node_addr(node) -> str | None:
    m = re.search(r"@([0-9a-fA-F]+)$", node.name or "")
    if not m:
        return None
    v = m.group(1).lower().lstrip("0")
    return v or "0"


def node_base(node) -> str:
    return re.sub(r"@.*$", "", node.name or "")


def compat_list(node) -> list[str]:
    v = node.props.get("compatible")
    if not v:
        return []
    if isinstance(v, str):
        return [v]
    return [s.decode("utf-8", "replace") for s in v.split(b"\x00") if s]


def domain_of(node, path: str = "") -> str:
    """Which subsystem a node belongs to.

    The node's own name is not enough: pinctrl state nodes are called
    'default', 'sleep', 'seta' and the display pipeline hangs off anonymous
    'port'/'endpoint' nodes.  Only the ancestor path says what they are, so
    the full path is matched first and the bare name only as a fallback.
    """
    hay = (path + " " + (node.name or "") + " " + " ".join(compat_list(node))).lower()
    for name, keys in DOMAINS:
        if any(k in hay for k in keys):
            return name
    return "其它"


def fmt(value, name: str = "") -> str:
    """Human-readable property value, truncated."""
    if value == b"":
        return "(empty)"
    try:
        s = render_value(name, value).strip()
    except Exception:
        return f"[{value[:16].hex(' ')}]"
    if s.startswith("="):
        s = s[1:].strip()
    if len(s) > 120:
        s = s[:117] + "..."
    return s


def brief(node, limit: int = 4) -> str:
    """One-line summary of a node: its compatibles plus a couple of key props."""
    bits = []
    cs = compat_list(node)
    if cs:
        bits.append("`" + "`, `".join(cs[:2]) + "`")
    for p in ("status", "dr_mode", "reg"):
        v = node.props.get(p)
        if v is not None and p != "reg":
            bits.append(f"{p}={fmt(v, p)}")
    return "  ".join(bits)


def walk_with_depth(root):
    out = []

    def rec(n, depth):
        out.append((n, depth))
        for c in n.children:
            rec(c, depth + 1)

    rec(root, 0)
    return out


def index_by_addr(root):
    d = defaultdict(list)
    for n in root.walk():
        a = node_addr(n)
        if a is not None:
            d[a].append(n)
    return d


def is_phandle_prop(name: str) -> bool:
    return name in PHANDLE_PROPS or name.endswith(PHANDLE_SUFFIXES)


ENABLED = {"okay", "ok"}
DISABLED = {"disabled", "fail", "fail-sss"}


def status_of(node) -> str:
    """Device tree spec: a missing status property means the device is enabled."""
    v = node.props.get("status")
    if v is None:
        return "okay"
    if isinstance(v, bytes):
        return v.rstrip(b"\x00").decode("utf-8", "replace") or "okay"
    return str(v) or "okay"


def diff_props(a, b) -> list[tuple[str, str, str]]:
    """Property-level differences between two nodes describing the same hw."""
    rows = []
    keys = sorted((set(a.props) | set(b.props)) - IGNORED_PROPS)
    for k in keys:
        va, vb = a.props.get(k), b.props.get(k)
        if va == vb:
            continue
        if is_phandle_prop(k) and va is not None and vb is not None:
            # Both point at something; the number itself is allocation order.
            continue
        rows.append(
            (k,
             "(absent)" if va is None else fmt(va, k),
             "(absent)" if vb is None else fmt(vb, k))
        )
    return rows


def pair_nodes(v_by_addr, o_by_addr, addrs):
    """Join nodes on @address, preferring pairs whose base names agree.

    Address alone is not enough: PMIC sub-devices and IOMMU contexts both sit
    at 0x1000 / 0x4000 / 0x5000, so a bare address join pairs a charger with
    an iommu context.  Require either the same node name or the same
    subsystem before pairing.
    """
    pairs = []
    for addr in addrs:
        best = None
        for a in v_by_addr[addr]:
            for b in o_by_addr[addr]:
                same_name = node_base(a) == node_base(b)
                same_dom = domain_of(a, a.path) == domain_of(b, b.path)
                if not (same_name or same_dom):
                    continue
                score = 2 if same_name else 1
                if best is None or score > best[0]:
                    best = (score, a, b)
        if best is not None:
            pairs.append((addr, best[1], best[2]))
    return pairs


def loose_key(node, dom: str) -> tuple[str, str] | None:
    """Coarse identity for nodes that describe the same controller block.

    The vendor tree names a node after the register block base, upstream
    names it after an offset inside that block: sdhci@07824000 vs
    mmc@7824900, 0x900 apart.  Both live in the same 64 KiB window, so the
    top four hex digits plus the subsystem are enough to say "same thing".

    Addresses below 64 KiB are excluded: PMIC sub-devices and SMD channels
    live at 0x5, 0xe, 0x94c and would all collapse into the same zero
    prefix, pairing unrelated nodes.
    """
    a = node_addr(node)
    if a is None:
        return None
    v = int(a, 16)
    if v < 0x10000:
        return None
    return (dom, f"{v:07x}"[:4])


def loose_pairs(v_by_addr, o_by_addr, v_addrs, o_addrs):
    """Second pass: pair leftovers that share a subsystem and address window."""
    found = []
    v_left = list(v_addrs)
    o_left = list(o_addrs)
    for va in list(v_left):
        matched = False
        for a in v_by_addr[va]:
            da = domain_of(a, a.path)
            ka = loose_key(a, da)
            if ka is None or matched:
                continue
            for ob in list(o_left):
                for b in o_by_addr[ob]:
                    if domain_of(b, b.path) != da:
                        continue
                    if loose_key(b, da) == ka:
                        found.append((va, a, b))
                        v_left.remove(va)
                        o_left.remove(ob)
                        matched = True
                        break
                if matched:
                    break
    return found, v_left, o_left


# Subsystems where a missing node or a changed setting actually breaks
# something a user can notice.  A missing coresight funnel does not.
CRITICAL_DOMAINS = ("USB", "网络", "存储", "SIM/Modem", "GPIO/按键/LED")


def build_report(vendor_path: Path, ours_path: Path, only: str | None) -> str:
    V, _ = dtb_dump.parse(str(vendor_path))
    O, _ = dtb_dump.parse(str(ours_path))

    v_nodes = walk_with_depth(V)
    o_nodes = walk_with_depth(O)
    v_by_addr = index_by_addr(V)
    o_by_addr = index_by_addr(O)

    # Hardware present in both trees, joined on @address.
    shared = sorted(set(v_by_addr) & set(o_by_addr), key=lambda x: (len(x), x))
    v_only = sorted(set(v_by_addr) - set(o_by_addr), key=lambda x: (len(x), x))
    o_only = sorted(set(o_by_addr) - set(v_by_addr), key=lambda x: (len(x), x))
    pairs = pair_nodes(v_by_addr, o_by_addr, shared)

    # Exact address joins miss controllers that the two trees name after
    # different offsets inside the same block, so run a looser second pass
    # before calling anything "missing".
    loose, v_only, o_only = loose_pairs(v_by_addr, o_by_addr, v_only, o_only)
    pairs.extend(loose)

    v_dom = defaultdict(list)
    for n, d in v_nodes:
        v_dom[domain_of(n, n.path)].append((n, d))
    o_dom = defaultdict(list)
    for n, d in o_nodes:
        o_dom[domain_of(n, n.path)].append((n, d))

    out: list[str] = []
    w = out.append

    w(f"# 设备树对照：vendor vs 在用\n")
    w(f"- vendor: `{vendor_path.name}` — {len(v_nodes)} 节点，"
      f"{len(v_by_addr)} 个带地址")
    w(f"- ours  : `{ours_path.name}` — {len(o_nodes)} 节点，"
      f"{len(o_by_addr)} 个带地址")
    w(f"- 地址匹配 **{len(shared)}** 个硬件控制器；仅 vendor {len(v_only)}，"
      f"仅 ours {len(o_only)}\n")

    if loose:
        w(f"另有 **{len(loose)}** 个控制器两边都有，但节点名里的地址写法不同"
          f"（一边写寄存器块基址、一边写块内偏移），已按同一硬件合并对比：\n")
        w("| vendor 节点 | ours 节点 |")
        w("|---|---|")
        for addr, a, b in loose:
            w(f"| `{a.name}` | `{b.name}` |")
        w("")

    # --- highlights ---------------------------------------------------------
    if not only:
        # A device the vendor tree has enabled but ours disables is the one
        # failure mode worth leading with.  Per the DT spec a missing status
        # means "okay", and the vendor tree relies on that heavily.
        turned_off = []
        key_rows = []
        for addr, a, b in pairs:
            sa, sb = status_of(a), status_of(b)
            if sa in ENABLED and sb in DISABLED:
                turned_off.append((addr, a, b, sa, sb))
            rows = [r for r in diff_props(a, b)
                    if r[0] in KEY_PROPS and r[0] != "status"]
            if rows:
                key_rows.append((addr, a, b, rows))

        crit_missing = defaultdict(list)
        for n, d in v_nodes:
            if node_addr(n) in set(v_only):
                dom = domain_of(n, n.path)
                if dom in CRITICAL_DOMAINS:
                    crit_missing[dom].append(n)

        w("## 重点发现\n")

        if turned_off:
            w("### vendor 启用、我们关掉了\n")
            w("按 DT 规范 `status` 缺失等于 `okay`，所以 vendor 树里没写 "
              "`status` 的节点在 Android 下是工作的。下面这些我们显式关掉了，"
              "逐个确认是有意为之还是漏了。\n")
            w("| 地址 | 节点 | 子系统 | vendor | ours |")
            w("|---|---|---|---|---|")
            for addr, a, b, sa, sb in turned_off:
                dom = domain_of(a, a.path)
                flag = "" if dom in CRITICAL_DOMAINS else "（非关键子系统）"
                w(f"| `@{addr}` | `{b.name}` | {dom}{flag} | {sa} | {sb} |")
            w("")
        else:
            w("### vendor 启用、我们关掉了\n\n没有这种情况。\n")

        if key_rows:
            w("### 其它关键属性差异\n")
            w("`dr_mode` / `bus-width` / `*-supply` 这类属性决定设备怎么接、"
              "能不能供上电，不一致就值得逐条确认。\n")
            w("| 地址 | vendor 节点 | ours 节点 | 差异 |")
            w("|---|---|---|---|")
            for addr, a, b, rows in key_rows:
                desc = "; ".join(f"`{k}` {va} → {vb}" for k, va, vb in rows[:3])
                desc = desc.replace("|", "\\|")
                w(f"| `@{addr}` | `{a.name}` | `{b.name}` | {desc} |")
            w("")
        else:
            w("### 其它关键属性差异\n\n没有差异。\n")

        if crit_missing:
            w("### 关键子系统里 vendor 有、我们没有\n")
            for dom in CRITICAL_DOMAINS:
                ns = crit_missing.get(dom)
                if not ns:
                    continue
                w(f"**{dom}**\n")
                for n in ns[:12]:
                    b = brief(n)
                    w(f"- `{n.path}`" + (f"  \n  {b}" if b else ""))
                if len(ns) > 12:
                    w(f"- …另有 {len(ns)-12} 个")
                w("")
        else:
            w("关键子系统里没有 vendor 独有的带地址节点。\n")

    # --- per-domain overview -------------------------------------------------
    w("## 各子系统节点数\n")
    w("| 子系统 | vendor | ours | 差额 |")
    w("|---|---:|---:|---:|")
    for name, _ in DOMAINS + [("其它", ())]:
        if only and name != only:
            continue
        vc = len(v_dom.get(name, []))
        oc = len(o_dom.get(name, []))
        if vc == 0 and oc == 0:
            continue
        delta = vc - oc
        w(f"| {name} | {vc} | {oc} | {delta:+d} |")
    w("")

    # --- shared hardware, property differences ------------------------------
    w("## 同一硬件，属性差异\n")
    w("按 `@地址` 配对。已排除 phandle、`#*-cells`、`clocks` 这类结构性噪音。\n")
    shown = 0
    for addr, a, b in pairs:
        if only and only not in (domain_of(a, a.path), domain_of(b, b.path)):
            continue
        rows = diff_props(a, b)
        if not rows:
            continue
        shown += 1
        w(f"### `@{addr}` — vendor `{a.name}` / ours `{b.name}`\n")
        w(f"- vendor 路径 `{a.path}`")
        w(f"- ours   路径 `{b.path}`\n")
        w("| 属性 | vendor | ours |")
        w("|---|---|---|")
        for k, va, vb in rows[:20]:
            va = va.replace("|", "\\|")[:110]
            vb = vb.replace("|", "\\|")[:110]
            w(f"| `{k}` | {va} | {vb} |")
        if len(rows) > 20:
            w(f"| … | 另有 {len(rows)-20} 条 | |")
        w("")
    if shown == 0:
        w("（该范围内没有属性差异）\n")

    # --- vendor-only nodes per domain --------------------------------------
    w("## vendor 有、我们没有的节点\n")
    w("按子系统分组。**不代表都要补** —— coresight、camera、adsp-loader "
      "这类是下游专有，主线没有对应驱动，缺了是正常的。\n")
    for name, _ in DOMAINS + [("其它", ())]:
        if only and name != only:
            continue
        items = [(n, d) for n, d in v_dom.get(name, []) if node_addr(n) in set(v_only)]
        if not items:
            continue
        w(f"### {name}（{len(items)} 个带地址节点）\n")
        for n, d in items[:40]:
            ind = "  " * 1
            b = brief(n)
            w(f"- `{n.path}`")
            if b:
                w(f"{ind}{b}")
        if len(items) > 40:
            w(f"- …另有 {len(items)-40} 个")
        w("")

    # --- ours-only ---------------------------------------------------------
    w("## 我们有、vendor 没有的节点\n")
    w("通常是上游新增的框架节点（opp-table、power-domain、iommu 上下文等），"
      "或是 Android 不需要的东西。\n")
    buckets = defaultdict(list)
    for addr in o_only:
        for n in o_by_addr[addr]:
            buckets[domain_of(n, n.path)].append(n)
    for name, _ in DOMAINS + [("其它", ())]:
        if only and name != only:
            continue
        ns = buckets.get(name, [])
        if not ns:
            continue
        w(f"- **{name}**（{len(ns)}）：" +
          ", ".join(f"`@{node_addr(n)}` {node_base(n)}" for n in ns[:12]) +
          (" …" if len(ns) > 12 else ""))
    w("")

    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("vendor", type=Path)
    ap.add_argument("ours", type=Path)
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--domain", help="only report this subsystem")
    args = ap.parse_args()

    text = build_report(args.vendor, args.ours, args.domain)
    if args.output:
        args.output.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {args.output} ({len(text):,} chars)")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
