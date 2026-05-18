# aqualux design spectrum

40 種設計風格的 aqualux 視覺光譜 — single-file HTML 集合。

**Live**: https://design.aqualux.dev（pending Netlify + CF DNS）

## Structure

```
.
├── index.html                          主圖鑑（40 work cards）
├── images/hero.png                     主圖鑑 hero 圖
├── works/
│   └── c14-cyberpunk/                  C14 賽博龐克 demo
│       ├── index.html                  完整 single-file 賽博龐克作品
│       └── images/                     20 張 gpt-image-2 生圖
└── netlify.toml
```

## How it was built

依 [reskin skill](https://github.com/chengchiehhuang-glitch/) 工作流：
- 從 [casper.tw Claude Skill 設計風格圖鑑](https://www.casper.tw/claude-skill-design-gallery/) 取得授權後復刻
- aqualux 紙感主索引（白底 + 紙色 + 髮絲線 + 柔灰藍 accent）
- 每子頁採用對應風格的視覺語彙（不套主品牌風格）
- 圖一律 gpt-image-2 重生

## Progress

| 狀態 | 內容 |
|---|---|
| ✅ | 主索引 40 卡片骨架 |
| ✅ | C14 賽博龐克 demo（20 張圖） |
| ⏳ | 其他 39 個子頁 |

## License

MIT for code structure / CSS implementation.
Original style framework inspired by Casper @ casper.tw（已取得授權）.

---

Curated by [Chengchieh Huang](https://aqualux.dev) · MMXXVI
