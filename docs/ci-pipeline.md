# CI 工作流梳理：从主线到固件

> 2026-10-18 整理。基于 `.github/workflows/` 下 8 个工作流的实际内容。

---

## 1. 两条路线，不要混

仓库里 8 个工作流分属两条互不相干的路线。

| 工作流 | 路线 | 产物 | 发布 |
|--------|------|------|------|
| `pmos-build.yml` | **A 产品线** | rootfs + boot.img + lk1st + EDL 工具 → zip | ✅ Release |
| `build-rootfs.yml` | A 产品线 | 同上，但不含 lk1st、不打包 zip | ✅ Release |
| `build_rndis_boot.yml` | A 产品线 | rootfs + boot.img | ❌ |
| `build-db410c.yml` | A 产品线（参考机型） | DB410c 镜像 | ❌ |
| `build-boot.yml` | **B 手工内核线** | 自制 boot.img | ❌ artifact |
| `mem-boot.yml` | B 手工内核线 | 自制 boot.img（initramfs 里 sleep 30） | ❌ artifact |
| `build-kernel.yml` | B 手工内核线 | 内核 Image.gz + dtbs | ❌ artifact |
| `build-lk1st.yml` | 引导器 | 签名后的 lk1st .mbn | ❌ artifact |

**只有 A 线出"能刷的固件"**，B 线是调试/验证用的。

---

## 2. "主线"具体指什么

| 层 | 上游 | 版本 | 谁拉 |
|----|------|------|------|
| 内核 | `github.com/msm8916-mainline/linux` | `v6.6-msm8916` | pmaports 的 `linux-postmarketos-qcom-msm8916` 包 |
| 用户态 | `gitlab.postmarketos.org/postmarketOS/pmaports` | `edge`（`--depth=1` 最新） | 工作流自己 clone |
| 构建器 | `gitlab.postmarketos.org/postmarketOS/pmbootstrap` | 最新 | 工作流自己 clone |
| 引导器 | `github.com/msm8916-mainline/lk2nd` | 默认 HEAD | 工作流自己 clone |

关键认知：**A 线不自己编内核**。内核是 pmaports 里的 APKBUILD 去拉主线源码编的，
我们只贡献 `config/device-testing/` 里的设备包（deviceinfo + DTB + APKBUILD）。

---

## 3. `pmos-build.yml` 八步

```
1. checkout                  fetch-depth: 0
2. apt 依赖                  kpartx coreutils parted e2fsprogs procps kmod + modprobe loop
3. 装 pmbootstrap            clone → /usr/local/bin/pmbootstrap
4. 编 lk1st                  lk2nd → make lk1st-msm8916 → qtestsign 签名
                             → out/lk1st-msm8916.mbn
5. 编 rootfs + 镜像          pmaports → 覆盖 overlay → 写 pmbootstrap_v3.cfg
                             → pmbootstrap --as-root install --password pmos --no-fde
                             → pmbootstrap --as-root shutdown
6. 收集打包                  find $WORK 所有 *.img（排除 cache）
                             + lk1st.mbn + 两个 .bat + flash_tools/edl/*
                             + tools/edl/readme.txt → zip
7. 发布                      softprops/action-gh-release → v2024.08-msm8916-full
8. 收尾                      echo
```

### 几个容易看漏的设计

- **`printf '8\n' > "$WORK/version"`** —— 伪造 pmbootstrap work 目录版本号，
  跳过首次运行向导，否则 CI 会卡在交互提问。
- **`git update-ref refs/remotes/origin/main HEAD`** —— pmbootstrap 要求 pmaports
  是官方 `origin/main`，`--depth=1` clone 后没有这个 ref，不补上会报错/警告。
- **overlay 合并到 `device/testing/`** —— 不是 `device/main/`。deviceinfo 里没有
  显式分类，pmaports 按目录判断；放错目录 `pmbootstrap` 找不到设备。
- **`pmbootstrap shutdown`** —— 卸载 loop 设备，否则后面的 `find`/`stat` 可能卡住。
- **`--as-root`** —— CI runner 里 pmbootstrap 需要 root 做 chroot 和 loop 挂载。

---

## 4. 已踩过并修好的坑

| 现象 | 根因 | 修法 |
|------|------|------|
| zip 只有 117 KB | 只 `find $WORK/output`，镜像实际写在别处 | 改 `find $WORK` 排除 cache，加 `IMG_COUNT` 硬校验 |
| lk1st 步骤 `Permission denied` | `git clone ... /src/lk2nd`，runner 不能建 `/src` | 改用 `$GITHUB_WORKSPACE/build/` |
| `mkbootimg: not found`（exit 127） | 容器 `jackadam/pmos_build:260715` 没装 | 加 apt/apk/dnf 兜底安装 |
| 镜像起不来但 CI 全绿 | heredoc 在 YAML `run: \|` 里把缩进写进 init，shebang 前带空格 | 改 `printf '%s\n'` 逐行写，加 `head -1 \| cat -A` 验证 |

---

## 5. 现在还不一致的地方

这些不影响"能不能编出来"，但会让产物行为对不上，建议逐个收掉。

### 5.1 两条路线用的 DTB 不是同一个

```
deviceinfo:        deviceinfo_dtb="qcom/msm8916-zhihe-ufi003-mb-v02"
build-boot.yml:    DTB=.../qcom/msm8916-thwc-ufi001c.dtb
mem-boot.yml:      DTB=.../qcom/msm8916-thwc-ufi001c.dtb
```

A 线用我们自己的 DTB，B 线用上游 UFI001C 的 DTB。B 线编出来的 boot.img
跑在 UFI003 上，硬件描述是错的（LED、USB、WiFi 都可能不对）。

### 5.2 boot.img 的内存布局两套

```
deviceinfo:  base 0x80000000  kernel 0x00080000  ramdisk 0x02000000
             second 0x00f00000  tags 0x01e00000
build-boot:  base 0x80000000  kernel 0x01000000  ramdisk 0x03000000
             dtb 0x05000000     tags 0x0010000
```

偏移差得很远。有 lk2nd 兜着可能都能起，但至少有一个是错的，得实测确认。

### 5.3 `variant` 输入是摆设

`pmos-build.yml` 有 `variant` 输入（phosh / sxmo …），但它只出现在 Release 标题里，
`pmbootstrap --as-root install` 没带 `--ui`。**选 sxmo 编出来的还是 phosh。**

### 5.4 `verify_osdesc.py` 是空转

`build_rndis_boot.yml` 最后跑 `python scripts/verify_osdesc.py`，但它校验的文件
CI 根本不生成。看起来在验证，实际什么都没验。

### 5.5 推代码不会触发编译

除 `build-db410c.yml`（只监听自己的文件）外，全部是 `workflow_dispatch`。
推送代码不会自动跑 CI，必须手动 dispatch —— 这也是为什么 `12e8b99`、`d3fb484`
两个提交一直没被编译过。

### 5.6 补丁失败被吞掉

B 线里 `git am ... || true`，补丁打不上也照样往下走，编出来的内核缺补丁而不自知。

### 5.7 `build_rndis_boot.yml.bak` 留在目录里

不影响执行，但容易让人误以为有两个 RNDIS 工作流。

---

## 6. 当前状态

- 最近一次成功：run `39069679774`（commit `60e1c1c`），产出
  `v2024.08-msm8916-full` / `msm8916-pmos-fullcompile.zip` 264.1 MiB
- 另一个 Release `v2024.08-msm8916` 是分开的 rootfs 578.0 MiB + boot.img 22.1 MiB
- 本地 `12e8b99`、`d3fb484` 未推送，CI 未见过
- **RNDIS 的 `usb-lan.sh` 不在任何产物里** —— 设备包没安装它，刷机后仍是 `02/06/00`
