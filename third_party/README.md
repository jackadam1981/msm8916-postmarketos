# Third-Party Sources

External source trees are kept outside git history. On the build host they currently live under:

```text
/home/jack/work/msm8916-standard-linux/third_party/
```

Current source checkouts:

| Source | Location | Upstream | State |
| --- | --- | --- | --- |
| lk2nd | `third_party/lk2nd` | `https://github.com/msm8916-mainline/lk2nd.git` | git shallow clone, `main`, `ce7fc78` |
| pmaports | `third_party/pmaports` | `https://gitlab.postmarketos.org/postmarketOS/pmaports.git` | git shallow clone, `main`, `02ad959` |
| pmbootstrap | `third_party/pmbootstrap` | `https://gitlab.postmarketos.org/postmarketOS/pmbootstrap` | archive from `main`, no git history |

The Linux kernel tree is intentionally not cloned yet. It is large, and the exact source should be chosen after the first device target and build strategy are clear.
