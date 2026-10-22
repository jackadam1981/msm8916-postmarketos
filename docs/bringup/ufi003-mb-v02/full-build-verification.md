# 完整内核包构建与产物验证

第一次把 `linux-postmarketos-qcom-msm8916` 完整编一遍，并从 Release 里把产物拆开核对。
记录时间 2026-10-22。

## 结论

内核包、boot.img、rootfs、刷机脚本全部产出且互相自洽。构建过程中发现两个
打包/刷机层面的问题，都已修掉（见「发现的问题」）。

| 项目 | 结果 |
|---|---|
| CI run | `39731246387`，commit `aecb6cc8` |
| 总耗时 | 43 分钟（内核编译 37.5 分钟） |
| 内核包 | `linux-postmarketos-qcom-msm8916-6.12.1-r9.apk` |
| boot.img | 23,175,168 B |
| 其中 dtb | kernel+9,283,832，50,361 B，443 节点 |
| rootfs | 802,160,640 B，纯 ext4，无嵌套 GPT |
| Release | `v2024.08-msm8916-full`，zip 281,833,945 B |

## 怎么确认内核真的重编了

`pkgrel` 从 8 bump 到 9，高于二进制仓库里的版本，所以 `pmbootstrap build`
必须重编而不是拉现成 apk。日志能对上：

```
[06:01:51] => edge/linux-postmarketos-qcom-msm8916: Building package (cross compiling: cross-native)
[06:39:22] Zapping buildroots
[06:39:23] => edge/linux-postmarketos-qcom-msm8916: Done!
=== checking .../linux-postmarketos-qcom-msm8916-6.12.1-r9.apk ===
=== DTB present in kernel package ===
```

`r9` 就是本地 bump 的版本号；`boot/dtbs/qcom/msm8916-zhihe-ufi003-mb-v02.dtb`
通过了 workflow 里 `tar -tzf | grep` 的硬校验。

## boot.img 里的 dtb 和 CI 编的是同一棵

`deviceinfo_append_dtb="true"` 让 dtb 贴在 kernel 尾部，所以 `kernel_size`
包含 Image + dtb，`second_size` 是 0。用 `tools/dtb/bootimg_dtb.py` 从产物
里提出来，和 dt-verify 那轮编的 dtb 逐字节比对：

```
dtb size   50,361 B（两处一致）
sha256     9666422fb636bc8de9deb03c258e45b3fe46e30aab8bf519db99a27d0b2c742f（两处一致）
cmp        IDENTICAL
verify_dtb OK: 19 board-specific assertions passed
```

也就是说：dts 源码 → CI 编出的 dtb → 最终进 boot.img 的 dtb，三者完全一致，
中间没有经过任何替换。

## rootfs 是纯 ext4，不是整盘镜像

`--split` 生效后 pmbootstrap 直接产出分区镜像，`carve_rootfs.py` 返回 2
（"already a plain ext4 image"）。实测：

```
410stick-ufi003-mb-v02-root.img  802,160,640 B  ext4_magic=0xef53  gpt_at_512=False
```

`gpt_at_512=False` 是关键——之前那个「整盘镜像写进 userdata」的 bug 就是
偏移 512 处有 `EFI PART`，内核找不到根文件系统。

## 发现的问题

### 1. 刷机脚本会把 /boot 分区当成 rootfs 写进 userdata

`--split` 会产出两个 ext4 分区镜像：

```
410stick-ufi003-mb-v02-boot.img   512 MiB   /boot 分区
410stick-ufi003-mb-v02-root.img   802 MiB   根文件系统
```

两个都以 `.img` 结尾。原来自动识别的逻辑是「名字不叫 `boot.img` 就用」：

```bat
if /i not "%%~nxf"=="boot.img" set "ROOTFS=%%~ff"
```

`410stick-ufi003-mb-v02-boot.img` 的名字不是 `boot.img`，所以通过了过滤；
而按目录序它排在 `-root.img` 前面，于是 `ROOTFS` 被设成了那个 512 MiB 的
/boot 分区。真刷下去就是把一个空的 /boot 写进 userdata，内核找不到 init，
设备停在启动阶段。

修法：先按名字精确找 `*-root.img`，再兜底匹配「既不是 `boot.img` 也不是
`*-boot.img`」的镜像。三种目录形态都实测过：

| 目录内容 | 选中的 |
|---|---|
| `boot.img` + `-boot.img` + `-root.img` | `-root.img` |
| `boot.img` + `-boot.img` + `my-rootfs.img` | `my-rootfs.img` |
| 只有 `boot.img` + `-boot.img` | 空（预检报错，不硬刷） |

`flash_edl_original.bat` 和 `flash_edl_secondary.bat` 都有这个问题，都改了。

### 2. 打包时不该带那个 512 MiB 的 /boot 镜像

没有任何一步会刷它——内核和 initramfs 都在 23 MiB 的 Android boot.img 里，
写进 32 MiB 的 boot 分区。它留在 zip 里既占地方，又是上面那个 bug 的成因。
`pmos-build.yml` 的打包步骤现在直接删掉它，并且要求 `*-root.img` 必须存在，
否则 fail。

## 怎么复现这套验证

```bash
# 1. 从 Release 拿 zip（281,833,945 B）
# 2. 看 boot.img 头 + dtb 位置
python tools/dtb/bootimg_dtb.py info boot.img
# 3. 提出 dtb 并断言
python tools/dtb/bootimg_dtb.py extract boot.img -o out/
python tools/dtb/verify_dtb.py out/msm8916-zhihe-ufi003-mb-v02.dtb
# 4. 确认 rootfs 是纯 ext4
python - <<'PY'
import struct
f=open('410stick-ufi003-mb-v02-root.img','rb'); f.seek(1024+0x38)
print(hex(struct.unpack('<H', f.read(2))[0]))   # 0xef53
PY
```

## 已知的边界

- 只验证了产物结构，没有在真机上跑。`verify_dtb.py` 的 19 项断言覆盖的是
  启动必须成立的板级配置，不是运行时行为。
- 音频仍未确认：vendor 用 GPIO 12 驱动外部功放，我们走 DB410c 的 sndcard。
- `410stick-ufi003-mb-v02-boot.img`（512 MiB ext4 /boot）已从包里去掉，
  但 pmbootstrap 每次仍会生成它，属于 `--split` 的固有行为。
