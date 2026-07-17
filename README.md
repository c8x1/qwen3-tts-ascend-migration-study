# Qwen3-TTS → Ascend 910B Migration Study

本仓库研究 Qwen3-TTS 训练工程迁移到华为 Ascend 910B 所需的成熟参考项目、训练知识和源码映射。

## Template preview

```bash
npm install
npx playwright install chromium
npm run serve
```

Open `http://127.0.0.1:4173/site/`.

## Tests

```bash
npm test
```

## Template behavior

- Desktop: both sidebars expanded by default
- Laptop: evidence sidebar collapsed by default
- Mobile: both sidebars open as drawers
- Collapsed rails: real keyboard-focusable destinations with visible tooltips
- Chapter tree: reusable nested disclosures with automatic current-path expansion
- Mobile header: current chapter plus a focusable search control
- Source excerpts: copy action and immutable official GitHub line links
- No JavaScript: complete navigation, article, evidence, links, and search form remain readable
- Shortcuts: `Alt+[` and `Alt+]`
- Runtime: local static HTML/CSS/JavaScript only

## Scope boundary

The repository studies existing migration projects. It does not claim that Qwen3-TTS training has been ported or validated on Ascend 910B.
