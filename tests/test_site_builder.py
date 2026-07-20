import copy
import csv
import json
import re
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

from scripts import build_site as build_site_cli
from scripts.phase2_contracts import Evidence
from scripts.site_builder import (
    build_search_documents,
    build_site,
    decision_href,
    load_all_indexes,
    load_page_catalogs,
    relative_href,
    render_page,
    script_safe_json,
    validate_catalogs,
)


ROOT = Path(__file__).resolve().parents[1]
TARGET_CATALOGS = [
    ROOT / "content/site-foundation.json",
    ROOT / "content/target-architecture.json",
]
FULL_TARGET_CATALOGS = [
    ROOT / "content/site-foundation.json",
    ROOT / "content/target-architecture.json",
    ROOT / "content/target-training.json",
]
TARGET_FIXED_PREFIX = (
    "https://github.com/QwenLM/Qwen3-TTS/blob/"
    "022e286b98fbec7e1e916cb940cdf532cd9f488e/"
)
TARGET_PAGE_CONTRACTS = {
    "target/package-inference-api.html": {
        "order": 2,
        "title": "包结构与推理 API",
        "sections": {
            "package-layout": {
                "TGT-PKG-001", "TGT-PKG-002", "TGT-PKG-003",
                "TGT-PKG-004", "TGT-PKG-005", "TGT-PKG-006",
            },
            "target-defaults": {"TGT-CLI-001", "TGT-CLI-002"},
            "load-chain": {"TGT-API-001"},
            "base-api": {"TGT-API-002"},
            "voice-design-api": {"TGT-API-003"},
            "custom-api": {"TGT-API-003"},
            "package-boundary": set(),
        },
        "call_chain": [
            ("公开入口", "qwen_tts/inference/qwen3_tts_model.py", "Qwen3TTSModel.from_pretrained"),
            ("注册配置", "qwen_tts/inference/qwen3_tts_model.py", "AutoConfig.register"),
            ("装载模型", "qwen_tts/inference/qwen3_tts_model.py", "AutoModel.from_pretrained"),
            ("装载处理器", "qwen_tts/inference/qwen3_tts_model.py", "AutoProcessor.from_pretrained"),
        ],
        "source_paths": {
            "pyproject.toml",
            "qwen_tts/core/__init__.py",
            "LICENSE",
            "MANIFEST.in",
            "qwen_tts/__init__.py",
            "qwen_tts/__main__.py",
            "qwen_tts/cli/demo.py",
            "qwen_tts/core/models/modeling_qwen3_tts.py",
            "qwen_tts/inference/qwen3_tts_model.py",
            "qwen_tts/inference/qwen3_tts_tokenizer.py",
        },
        "boundary": "package-boundary",
    },
    "target/model-architecture.html": {
        "order": 3,
        "title": "复合模型架构与生成流",
        "sections": {
            "composite-config": {"TGT-CONFIG-001"},
            "speaker-encoder": {"TGT-MODEL-001"},
            "talker": {"TGT-MODEL-002"},
            "code-predictor": {"TGT-MODEL-004"},
            "precision-islands": {"TGT-MODEL-005", "TGT-MODEL-006", "TGT-MODEL-007"},
            "generation-flow": {"TGT-MODEL-003", "TGT-TOK25-011"},
            "model-boundary": set(),
        },
        "call_chain": [
            ("包装器装载入口", "qwen_tts/inference/qwen3_tts_model.py", "Qwen3TTSModel.from_pretrained"),
            ("条件模型装载", "qwen_tts/core/models/modeling_qwen3_tts.py", "Qwen3TTSForConditionalGeneration.from_pretrained"),
            ("speech tokenizer 资源", "qwen_tts/core/models/modeling_qwen3_tts.py", "speech_tokenizer/*"),
            ("生成配置资源", "qwen_tts/core/models/modeling_qwen3_tts.py", "generation_config.json"),
        ],
        "source_paths": {
            "qwen_tts/core/models/configuration_qwen3_tts.py",
            "qwen_tts/core/models/modeling_qwen3_tts.py",
            "qwen_tts/inference/qwen3_tts_model.py",
        },
        "boundary": "model-boundary",
    },
    "target/tokenizer-12hz.html": {
        "order": 4,
        "title": "12Hz Tokenizer 契约",
        "sections": {
            "package-tokenizer-registry": {"TGT-PKG-002"},
            "configuration": {"TGT-TOK12-002"},
            "rate-derivation": {"TGT-TOK12-003"},
            "encode-contract": {"TGT-TOK12-001"},
            "rvq": {"TGT-TOK12-001"},
            "decode-contract": {"TGT-TOK12-001"},
            "training-gap": set(),
        },
        "call_chain": [
            ("12Hz encode 分支入口", "qwen_tts/core/tokenizer_12hz/modeling_qwen3_tts_tokenizer_v2.py", "Qwen3TTSTokenizerV2Model.encode"),
            ("Mimi encoder 分支", "qwen_tts/core/tokenizer_12hz/modeling_qwen3_tts_tokenizer_v2.py", "self.encoder.encode"),
        ],
        "source_paths": {
            "qwen_tts/core/__init__.py",
            "qwen_tts/core/tokenizer_12hz/configuration_qwen3_tts_tokenizer_v2.py",
            "qwen_tts/core/tokenizer_12hz/modeling_qwen3_tts_tokenizer_v2.py",
        },
        "boundary": "training-gap",
    },
    "target/tokenizer-25hz.html": {
        "order": 5,
        "title": "25Hz Tokenizer 静态依赖图",
        "sections": {
            "asset-inventory": {"TGT-TOK25-002"},
            "encoder-vq": {"TGT-TOK25-012", "TGT-TOK25-013"},
            "campplus-dependency": {"TGT-TOK25-003"},
            "speech-vq-dependencies": {"TGT-TOK25-004", "TGT-TOK25-005"},
            "whisper-attention": {"TGT-TOK25-006", "TGT-TOK25-007"},
            "vq-core": {"TGT-TOK25-009", "TGT-TOK25-010"},
            "dit-bigvgan": {"TGT-TOK25-001"},
            "decoder-precision": {"TGT-TOK25-008"},
            "main-model-assets": {"TGT-TOK25-011"},
            "asset-boundary": set(),
        },
        "call_chain": [
            ("25Hz encode 分支入口", "qwen_tts/core/tokenizer_25hz/modeling_qwen3_tts_tokenizer_v1.py", "Qwen3TTSTokenizerV1Model.encode"),
            ("编码器量化分支", "qwen_tts/core/tokenizer_25hz/modeling_qwen3_tts_tokenizer_v1.py", "Qwen3TTSTokenizerV1Encoder.quantize_speech"),
            ("波形转 mel 分支", "qwen_tts/core/tokenizer_25hz/modeling_qwen3_tts_tokenizer_v1.py", "Qwen3TTSTokenizerV1Encoder.speech2mel"),
            ("mel 转 code 分支", "qwen_tts/core/tokenizer_25hz/modeling_qwen3_tts_tokenizer_v1.py", "Qwen3TTSTokenizerV1Encoder.mel2code"),
        ],
        "source_paths": {
            "qwen_tts/core/tokenizer_25hz/modeling_qwen3_tts_tokenizer_v1.py",
            "qwen_tts/core/tokenizer_25hz/vq/speech_vq.py",
            "qwen_tts/core/tokenizer_25hz/vq/whisper_encoder.py",
            "qwen_tts/core/tokenizer_25hz/vq/core_vq.py",
            "qwen_tts/core/models/modeling_qwen3_tts.py",
        },
        "boundary": "asset-boundary",
    },
    "target/processor-contracts.html": {
        "order": 6,
        "title": "Processor 输入与提示词契约",
        "sections": {
            "text-contract": {"TGT-PROC-001"},
            "audio-wrapper": {"TGT-PROC-002"},
            "shape-contract": {"TGT-PROC-001", "TGT-PROC-002"},
            "prompt-contract": {"TGT-PROC-001", "TGT-PROC-002"},
            "migration-boundary": set(),
        },
        "call_chain": [
            ("ChatML 文本分支", "qwen_tts/core/models/processing_qwen3_tts.py", "Qwen3TTSProcessor.apply_chat_template"),
            ("文本 tokenizer 分支", "qwen_tts/core/models/processing_qwen3_tts.py", "Qwen3TTSProcessor.__call__"),
            ("文本 BatchFeature", "qwen_tts/core/models/processing_qwen3_tts.py", "BatchFeature"),
        ],
        "source_paths": {
            "qwen_tts/core/models/processing_qwen3_tts.py",
            "qwen_tts/inference/qwen3_tts_tokenizer.py",
            "qwen_tts/inference/qwen3_tts_model.py",
        },
        "boundary": "migration-boundary",
    },
}
TRAINING_PAGE_CONTRACTS = {
    "target/sft-data-collate.html": {
        "order": 7,
        "title": "SFT 数据预处理与 Collate",
        "sections": {
            "public-recipe": {"TGT-SCOPE-001"},
            "jsonl-contract": {"TGT-DATA-001"},
            "preprocess-device": {"TGT-DATA-003"},
            "offline-codes": {"TGT-DATA-001"},
            "dataset-item": {"TGT-DATA-002"},
            "collate-contract": {"TGT-DATA-002"},
            "data-boundary": {"TGT-DATA-002", "TGT-TRAIN-001", "TGT-TRAIN-006"},
        },
        "chains": {
            "offline-codes": [
                ("预处理入口", "finetuning/prepare_data.py", "prepare_data.main"),
                ("批量编码", "finetuning/prepare_data.py", "tokenizer_12hz.encode"),
                ("移回 CPU 并转列表", "finetuning/prepare_data.py", "code.cpu().tolist"),
                ("写入带 audio_codes 的 JSONL", "finetuning/prepare_data.py", "json.dumps / f.writelines"),
            ],
            "dataset-item": [
                ("读取样本", "finetuning/dataset.py", "TTSDataset.__getitem__"),
                ("构造 assistant 文本", "finetuning/dataset.py", "TTSDataset._build_assistant_text"),
                ("生成 text ids", "finetuning/dataset.py", "TTSDataset._tokenize_texts"),
                ("规范化参考音频", "finetuning/dataset.py", "TTSDataset._normalize_audio_inputs"),
                ("提取参考 mel", "finetuning/dataset.py", "TTSDataset.extract_mels"),
            ],
            "collate-contract": [
                ("batch 入口", "finetuning/dataset.py", "TTSDataset.collate_fn"),
                ("双轨输入与 codec 张量", "finetuning/dataset.py", "input_ids / codec_ids"),
                ("构造 embedding 与 attention masks", "finetuning/dataset.py", "text_embedding_mask / codec_embedding_mask / codec_mask / attention_mask"),
                ("构造 codec-0 labels", "finetuning/dataset.py", "codec_0_labels"),
            ],
        },
        "source_paths": {
            "finetuning/README.md",
            "finetuning/prepare_data.py",
            "finetuning/dataset.py",
        },
        "boundary": "data-boundary",
    },
    "target/sft-training-loop.html": {
        "order": 8,
        "title": "SFT 训练循环",
        "sections": {
            "target-precision-defaults": {"TGT-TRAIN-000"},
            "setup": {"TGT-TRAIN-000", "TGT-TRAIN-001", "TGT-TRAIN-005"},
            "prepared-model-access": {"TGT-TRAIN-002", "TGT-TRAIN-007"},
            "dataloader-sharding": {"TGT-TRAIN-006"},
            "embedding-flow": {"TGT-TRAIN-002"},
            "main-forward": {"TGT-MODEL-004", "TGT-TRAIN-005"},
            "sub-talker": {"TGT-MODEL-004", "TGT-TRAIN-005"},
            "training-loop": {"TGT-TRAIN-005"},
            "training-boundary": {"TGT-GAP-001"},
        },
        "chains": {
            "setup": [
                ("装载模型", "finetuning/sft_12hz.py", "Qwen3TTSModel.from_pretrained"),
                ("装载配置", "finetuning/sft_12hz.py", "AutoConfig.from_pretrained"),
                ("构造数据集", "finetuning/sft_12hz.py", "TTSDataset"),
                ("构造 DataLoader", "finetuning/sft_12hz.py", "DataLoader"),
                ("构造优化器", "finetuning/sft_12hz.py", "AdamW"),
                ("交给 Accelerate", "finetuning/sft_12hz.py", "accelerator.prepare"),
            ],
            "embedding-flow": [
                ("参考 mel 编码", "finetuning/sft_12hz.py", "model.speaker_encoder"),
                ("文本 embedding", "finetuning/sft_12hz.py", "model.talker.model.text_embedding"),
                ("codec-0 embedding", "finetuning/sft_12hz.py", "model.talker.model.codec_embedding"),
                ("写入 speaker slot", "finetuning/sft_12hz.py", "input_codec_embedding[:, 6, :] = speaker_embedding"),
                ("合成 text+codec-0", "finetuning/sft_12hz.py", "input_embeddings = input_text_embedding + input_codec_embedding"),
                ("读取残差 codec embedding", "finetuning/sft_12hz.py", "model.talker.code_predictor.get_input_embeddings"),
                ("应用 codec mask", "finetuning/sft_12hz.py", "codec_i_embedding * codec_mask.unsqueeze(-1)"),
                ("逐项加入残差 embedding", "finetuning/sft_12hz.py", "input_embeddings = input_embeddings + codec_i_embedding"),
            ],
            "main-forward": [
                ("Talker 主前向", "finetuning/sft_12hz.py", "model.talker"),
                ("主损失", "finetuning/sft_12hz.py", "outputs.loss"),
            ],
            "sub-talker": [
                ("筛选 Talker hidden states 与 codec ids", "finetuning/sft_12hz.py", "hidden_states[codec_mask[:, :-1]] / codec_ids[codec_mask]"),
                ("残差码本训练 helper", "qwen_tts/core/models/modeling_qwen3_tts.py", "model.talker.forward_sub_talker_finetune"),
                ("code predictor 前向", "qwen_tts/core/models/modeling_qwen3_tts.py", "code_predictor.forward_finetune"),
            ],
            "training-loop": [
                ("组合损失", "finetuning/sft_12hz.py", "outputs.loss + 0.3 * sub_talker_loss"),
                ("反向传播", "finetuning/sft_12hz.py", "accelerator.backward"),
                ("同步步裁剪梯度", "finetuning/sft_12hz.py", "accelerator.clip_grad_norm_"),
                ("参数更新", "finetuning/sft_12hz.py", "optimizer.step"),
                ("清空梯度", "finetuning/sft_12hz.py", "optimizer.zero_grad"),
            ],
        },
        "source_paths": {
            "finetuning/sft_12hz.py",
            "finetuning/dataset.py",
            "qwen_tts/core/models/modeling_qwen3_tts.py",
        },
        "boundary": "training-boundary",
    },
    "target/optimizer-checkpoint-export.html": {
        "order": 9,
        "title": "优化器、Checkpoint 与导出",
        "sections": {
            "accelerate-ownership": {
                "TGT-TRAIN-001", "TGT-TRAIN-003", "TGT-TRAIN-004",
                "TGT-TRAIN-006", "TGT-TRAIN-007",
            },
            "optimizer": {"TGT-TRAIN-005"},
            "repo-id-vs-local-path": {"TGT-EXPORT-002", "TGT-EXPORT-003"},
            "main-process-export": {"TGT-EXPORT-001"},
            "custom-speaker": {"TGT-EXPORT-001"},
            "checkpoint-gap": {"TGT-GAP-001"},
        },
        "chains": {
            "optimizer": [
                ("构造优化器", "finetuning/sft_12hz.py", "AdamW"),
                ("同步步裁剪梯度", "finetuning/sft_12hz.py", "accelerator.clip_grad_norm_"),
                ("参数更新", "finetuning/sft_12hz.py", "optimizer.step"),
                ("清空梯度", "finetuning/sft_12hz.py", "optimizer.zero_grad"),
            ],
            "main-process-export": [
                ("主进程门控", "finetuning/sft_12hz.py", "accelerator.is_main_process"),
                ("复制本地模型目录", "finetuning/sft_12hz.py", "shutil.copytree"),
                ("读取并改写 config.json", "finetuning/sft_12hz.py", "json.load / json.dump"),
                ("解包模型", "finetuning/sft_12hz.py", "accelerator.unwrap_model"),
                ("状态移到 CPU", "finetuning/sft_12hz.py", "unwrapped_model.state_dict"),
                ("移除 speaker encoder", "finetuning/sft_12hz.py", "del state_dict[speaker_encoder*]"),
                ("注入 speaker row 3000", "finetuning/sft_12hz.py", "codec_embedding.weight[3000] = target_speaker_embedding[0]"),
                ("写 safetensors", "finetuning/sft_12hz.py", "save_file"),
            ],
        },
        "source_paths": {"finetuning/sft_12hz.py"},
        "boundary": "checkpoint-gap",
    },
    "target/coverage-gaps.html": {
        "order": 10,
        "title": "目标覆盖矩阵与验证缺口",
        "sections": {
            "target-coverage": set(),
            "reference-roles": {"PH1-ROLE-MM", "PH1-ROLE-LLM", "PH1-ROLE-MOSS"},
            "environment-lanes": {"PH1-ENV-LANES", "TGT-HW-001"},
            "future-validation": {"PH1-ENV-LANES", "TGT-HW-001"},
            "deferred-plans": {"PH1-ENV-LANES", "TGT-HW-001"},
        },
        "chains": {
            "target-coverage": [
                ("审计输入（非官方调用链）", "research/target-coverage.csv", "35 exact CSV rows"),
                ("审计目录映射", "content/target-training.json", "target-coverage table"),
                ("静态站构建", "scripts/site_builder.py", "_render_table"),
                ("审计输出", "site/target/coverage-gaps.html", "35 data-coverage-path rows"),
            ],
        },
        "source_paths": {
            "research/target-coverage.csv",
            "research/reference-selection-proposal.md",
            "research/selected-revisions.csv",
        },
        "boundary": "deferred-plans",
    },
}


def minimal_catalog(block=None, text="x"):
    block = block or {
        "type": "paragraph",
        "text": text,
        "state": "verified",
        "evidence_ids": ["E-1"],
    }
    return {
        "schema_version": 1,
        "pages": [
            {
                "slug": "index.html",
                "title": "Title",
                "summary": "Summary",
                "order": 1,
                "group": "foundation",
                "objectives": ["Learn"],
                "prerequisites": ["PyTorch"],
                "sections": [
                    {"id": "intro", "title": "Intro", "blocks": [block]}
                ],
            }
        ],
    }


def fixture_indexes():
    return {
        "snap": {
            "files": [
                {
                    "path": "pkg/a.py",
                    "bytes": 4,
                    "sha256": "a" * 64,
                    "kind": "python",
                    "line_count": 2,
                }
            ],
            "symbols": [
                {
                    "id": "pkg/a.py:C:1",
                    "path": "pkg/a.py",
                    "qualname": "C",
                    "kind": "class",
                    "line": 1,
                    "end_line": 2,
                }
            ],
            "configs": [
                {
                    "id": "pkg/a.py:FLAG:2",
                    "path": "pkg/a.py",
                    "key": "FLAG",
                    "owner": "",
                    "kind": "python-assignment",
                    "line": 2,
                }
            ],
        }
    }


def fixture_evidence(decision_refs=()):
    return {
        "E-1": Evidence(
            "E-1",
            None,
            None,
            None,
            None,
            "verified",
            "claim",
            "",
            ("SRC-001",),
            decision_refs,
        )
    }


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"])
        attribute = "href" if tag in {"a", "link"} else "src" if tag == "script" else None
        if attribute and values.get(attribute):
            self.links.append(values[attribute])


class SiteBuilderTest(unittest.TestCase):
    def test_full_catalog_has_thirteen_pages_and_required_training_sections(self):
        catalogs = [
            ROOT / "content/site-foundation.json",
            ROOT / "content/target-architecture.json",
            ROOT / "content/target-training.json",
        ]
        pages = load_page_catalogs(catalogs)
        self.assertEqual([page["order"] for page in pages], list(range(1, 14)))
        serialized = json.dumps(pages, ensure_ascii=False)
        for text in [
            "finetuning/README.md",
            "TTSDataset.collate_fn",
            "outputs.loss + 0.3 * sub_talker_loss",
            "accelerator.prepare",
            "AdamW",
            "speaker row 3000",
            "CANN 8.5.2 兼容性：unknown",
        ]:
            self.assertIn(text, serialized)

    def test_training_catalog_has_exact_page_section_evidence_and_flow_contracts(self):
        pages = load_page_catalogs(FULL_TARGET_CATALOGS)
        targets = [page for page in pages if page["group"] == "target-training"]
        self.assertEqual(
            [(page["order"], page["slug"], page["title"]) for page in targets],
            [
                (contract["order"], slug, contract["title"])
                for slug, contract in TRAINING_PAGE_CONTRACTS.items()
            ],
        )

        for page in targets:
            with self.subTest(slug=page["slug"]):
                contract = TRAINING_PAGE_CONTRACTS[page["slug"]]
                sections = {
                    section["id"]: section for section in page["sections"]
                }
                self.assertEqual(set(sections), set(contract["sections"]))
                self.assertTrue(page["objectives"])
                self.assertEqual(
                    page["prerequisites"],
                    ["熟悉 PyTorch 单卡张量与训练循环"],
                )

                for section_id, expected_evidence in contract["sections"].items():
                    actual_evidence = set()
                    for block in sections[section_id]["blocks"]:
                        actual_evidence.update(block.get("evidence_ids", []))
                        for item in block.get("items", []):
                            actual_evidence.update(item.get("evidence_ids", []))
                    self.assertEqual(
                        actual_evidence,
                        expected_evidence,
                        f"{page['slug']}#{section_id}: "
                        f"expected {expected_evidence}, got {actual_evidence}",
                    )

                for section_id, expected_chain in contract["chains"].items():
                    chains = [
                        block
                        for block in sections[section_id]["blocks"]
                        if block["type"] == "call_chain"
                    ]
                    self.assertEqual(len(chains), 1)
                    self.assertEqual(
                        [
                            (item["label"], item["path"], item["symbol"])
                            for item in chains[0]["items"]
                        ],
                        expected_chain,
                    )

                source_tables = [
                    block
                    for section in page["sections"]
                    for block in section["blocks"]
                    if block["type"] == "table"
                    and "源码路径" in block["headers"]
                    and block["rows"]
                ]
                self.assertTrue(source_tables)
                actual_source_paths = {
                    row[table["headers"].index("源码路径")]
                    for table in source_tables
                    for row in table["rows"]
                }
                self.assertTrue(
                    contract["source_paths"] <= actual_source_paths,
                    f"{page['slug']}: missing source paths "
                    f"{contract['source_paths'] - actual_source_paths}",
                )
                self.assertTrue(sections[contract["boundary"]]["blocks"])

    def test_training_facts_keep_verified_inference_and_pending_boundaries(self):
        pages = {
            page["slug"]: page for page in load_page_catalogs(FULL_TARGET_CATALOGS)
        }

        def section(slug, section_id):
            return next(
                item for item in pages[slug]["sections"]
                if item["id"] == section_id
            )

        data_page = json.dumps(
            pages["target/sft-data-collate.html"], ensure_ascii=False
        )
        for text in (
            "12Hz Base",
            "single-speaker",
            "audio/text/ref_audio",
            "audio_codes",
            "cuda:0",
            "device_map=args.device",
            "(T,16)",
            "24kHz",
            "128-bin",
            "(B,T,2)",
            "codec-0 labels",
            "不作 bucketing 声明",
        ):
            self.assertIn(text, data_page)
        self.assertNotIn("prepare_data 会自动选择可用 GPU", data_page)
        self.assertNotIn("dataset 内部执行在线 tokenizer.encode", data_page)

        training_page = pages["target/sft-training-loop.html"]
        training_json = json.dumps(training_page, ensure_ascii=False)
        self.assertIn("DataLoader sharding 交给 Accelerate runtime", training_json)
        self.assertIn("wrapper/version/multi-process behavior", training_json)
        self.assertIn("pending execution", training_json)
        prepared = section(
            "target/sft-training-loop.html", "prepared-model-access"
        )
        prepared_paragraphs = [
            block for block in prepared["blocks"]
            if block["type"] == "paragraph"
        ]
        self.assertEqual(
            {block["state"] for block in prepared_paragraphs},
            {"verified", "inference"},
        )
        sharding = section(
            "target/sft-training-loop.html", "dataloader-sharding"
        )
        self.assertEqual(sharding["blocks"][0]["state"], "inference")
        for forbidden in (
            "没有 distributed sampler，所以不分布式",
            "no distributed sampler means no distribution",
            "prepared model attributes 会失败",
            "global speaker embedding 跨进程共享",
            "训练已成功",
            "validation loss",
            "resume 成功",
        ):
            self.assertNotIn(forbidden, training_json)

        export_page = pages["target/optimizer-checkpoint-export.html"]
        export_json = json.dumps(export_page, ensure_ascii=False)
        for text in (
            "Hugging Face repo ID",
            "实际导出静态上需要本地目录",
            "accelerator.is_main_process",
            "speaker row 3000",
            "drop speaker encoder",
            "safetensors 不等于 optimizer/RNG resume",
        ):
            self.assertIn(text, export_json)
        ownership = section(
            "target/optimizer-checkpoint-export.html", "accelerate-ownership"
        )
        self.assertEqual(
            {
                block["state"]
                for block in ownership["blocks"]
                if block["type"] == "paragraph"
            },
            {"verified", "inference"},
        )
        ownership_verified = next(
            block for block in ownership["blocks"]
            if block["type"] == "paragraph" and block["state"] == "verified"
        )
        self.assertEqual(ownership_verified["evidence_ids"], ["TGT-TRAIN-001"])
        self.assertIn("accelerator.prepare", ownership_verified["text"])
        for out_of_range_claim in (
            "accumulate", "backward", "clip", "print", "is_main_process",
            "unwrap_model",
        ):
            self.assertNotIn(out_of_range_claim, ownership_verified["text"])

        custom_speaker = section(
            "target/optimizer-checkpoint-export.html", "custom-speaker"
        )
        custom_verified = next(
            block for block in custom_speaker["blocks"]
            if block["type"] == "paragraph" and block["state"] == "verified"
        )
        self.assertNotIn("process-local pending", custom_verified["text"])

        coverage_json = json.dumps(
            pages["target/coverage-gaps.html"], ensure_ascii=False
        )
        self.assertIn(
            "审计/构建 provenance，非官方 Qwen3-TTS 调用链",
            coverage_json,
        )
        for text in (
            "文档覆盖完成",
            "源码静态核验",
            "项目声明",
            "硬件待验证",
            "MindSpeed-MM",
            "MindSpeed-LLM",
            "MOSS-TTS",
            "project-native",
            "2.7.1 + CANN 8.5.0",
            "target",
            "2.7.1 + CANN 8.5.2",
            "CANN 8.5.2 兼容性：unknown",
            "本页不是迁移方案",
            "本研究没有运行 CUDA、NPU、训练、推理或评测",
        ):
            self.assertIn(text, coverage_json)
        for forbidden in (
            "project-native 已复现",
            "项目原生车道已复现",
            "CANN 8.5.2 已兼容",
            "CANN 8.5.2 已跑通",
            "MindSpeed-LLM 支持 TTS scale",
            "MOSS-TTS 提供 Ascend training",
        ):
            self.assertNotIn(forbidden, coverage_json)

    def test_coverage_research_methodology_is_inference_not_project_claim(self):
        pages = {
            page["slug"]: page for page in load_page_catalogs(FULL_TARGET_CATALOGS)
        }
        coverage = pages["target/coverage-gaps.html"]
        environment_lanes = next(
            section for section in coverage["sections"]
            if section["id"] == "environment-lanes"
        )
        methodology = next(
            block for block in environment_lanes["blocks"]
            if block["type"] == "paragraph"
            and block["text"].startswith("状态层次必须分开")
        )
        self.assertEqual(methodology["state"], "inference")

    def test_site_builder_joins_newlines_outside_f_string_expressions(self):
        source = (ROOT / "scripts/site_builder.py").read_text(encoding="utf-8")
        self.assertNotIn(r"{'\n'.join(", source)
        self.assertIn('rendered_rows = "\\n".join(rows)', source)
        self.assertIn('rendered_sections = "\\n".join(sections)', source)
        self.assertIn("{rendered_rows}</tbody>", source)
        self.assertIn("{rendered_sections}", source)

    def test_coverage_catalog_rows_match_target_coverage_csv_exactly(self):
        pages = {
            page["slug"]: page for page in load_page_catalogs(FULL_TARGET_CATALOGS)
        }
        coverage = pages["target/coverage-gaps.html"]
        section = next(
            item for item in coverage["sections"]
            if item["id"] == "target-coverage"
        )
        table = next(
            block for block in section["blocks"]
            if block["type"] == "table" and block["headers"][0] == "path"
        )
        with (ROOT / "research/target-coverage.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            reader = csv.DictReader(handle)
            expected_headers = reader.fieldnames
            expected_rows = [
                [row[header] for header in expected_headers] for row in reader
            ]
        self.assertEqual(table["headers"], expected_headers)
        self.assertEqual(table["rows"], expected_rows)
        self.assertEqual(len(table["rows"]), 35)
        self.assertEqual(
            len({row[0] for row in table["rows"]}), len(table["rows"])
        )

    def test_coverage_path_attribute_is_derived_only_for_coverage_table(self):
        rows = [[f"path-{index}&.py", "mapped"] for index in range(35)]
        coverage_page = minimal_catalog(
            block={
                "type": "table",
                "headers": ["path", "disposition"],
                "rows": rows,
            }
        )["pages"][0]
        coverage_page["sections"][0]["id"] = "target-coverage"
        html = render_page(
            coverage_page, [coverage_page], fixture_evidence(), []
        )
        self.assertEqual(html.count("data-coverage-path="), 35)
        self.assertEqual(
            sum(
                "data-coverage-path=" in line
                for line in html.splitlines()
            ),
            35,
        )
        self.assertIn('data-coverage-path="path-0&amp;.py"', html)

        ordinary_page = minimal_catalog(
            block={
                "type": "table",
                "headers": ["path", "disposition"],
                "rows": [["a&b.py", "mapped"]],
            }
        )["pages"][0]
        ordinary_html = render_page(
            ordinary_page, [ordinary_page], fixture_evidence(), []
        )
        self.assertNotIn("data-coverage-path", ordinary_html)

    def test_generated_full_site_has_exact_coverage_navigation_search_and_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            built = build_site(output, FULL_TARGET_CATALOGS)
            html_paths = [path for path in built if path.suffix == ".html"]
            self.assertEqual(len(html_paths), 13)
            self.assertEqual(len(built), 14)

            pages = load_page_catalogs(FULL_TARGET_CATALOGS)
            self.assertEqual([page["order"] for page in pages], list(range(1, 14)))
            expected_nav = [(page["order"], page["title"]) for page in pages]
            external = json.loads(
                (output / "assets/search-index.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(len(external), 47_504)
            search_html = (output / "search.html").read_text(encoding="utf-8")
            match = re.search(
                r'<script id="search-data" type="application/json">(.*?)</script>',
                search_html,
                re.DOTALL,
            )
            self.assertIsNotNone(match)
            self.assertEqual(json.loads(match.group(1)), external)

            for index, path in enumerate(html_paths):
                html = path.read_text(encoding="utf-8")
                nav = re.search(
                    r'<ul id="chapter-tree" class="chapter-tree">(.*?)</ul>',
                    html,
                    re.DOTALL,
                )
                self.assertIsNotNone(nav)
                self.assertEqual(
                    [
                        (int(order), title)
                        for order, title in re.findall(
                            r">(\d+) · ([^<]+)</a>", nav.group(1)
                        )
                    ],
                    expected_nav,
                )
                self.assertEqual('rel="prev"' in html, index > 0)
                self.assertEqual('rel="next"' in html, index + 1 < len(html_paths))

                parser = LinkParser()
                parser.feed(html)
                self.assertEqual(len(parser.ids), len(set(parser.ids)))
                for href in parser.links:
                    if href.startswith("#"):
                        self.assertIn(href[1:], parser.ids)
                        continue
                    if href.startswith(("http://", "https://", "mailto:")):
                        continue
                    target_text, _, fragment = href.partition("#")
                    target_text = target_text.split("?", 1)[0]
                    if not target_text.endswith(".html"):
                        continue
                    target = (path.parent / target_text).resolve()
                    self.assertTrue(
                        target.is_file(),
                        f"{path.relative_to(output)} -> {href}",
                    )
                    if fragment:
                        target_parser = LinkParser()
                        target_parser.feed(target.read_text(encoding="utf-8"))
                        self.assertIn(fragment, target_parser.ids)

            coverage_html = (
                output / "target/coverage-gaps.html"
            ).read_text(encoding="utf-8")
            paths = re.findall(
                r'data-coverage-path="([^"]+)"', coverage_html
            )
            with (ROOT / "research/target-coverage.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                expected_paths = [row["path"] for row in csv.DictReader(handle)]
            self.assertEqual(paths, expected_paths)
            self.assertEqual(len(paths), 35)
            self.assertEqual(len(paths), len(set(paths)))
            self.assertEqual(
                sum(
                    "data-coverage-path=" in line
                    for line in coverage_html.splitlines()
                ),
                35,
            )
            for literal in (
                "本页不是迁移方案",
                "本研究没有运行 CUDA、NPU、训练、推理或评测",
                "CANN 8.5.2 兼容性：unknown",
            ):
                self.assertIn(literal, coverage_html)

            source_html = (
                output / "indexes/source-files.html"
            ).read_text(encoding="utf-8")
            self.assertRegex(
                source_html, r"MindSpeed-MM.*codeload archive"
            )
            self.assertRegex(
                source_html, r"MindSpeed-LLM.*codeload archive"
            )
            self.assertNotRegex(source_html, r"MindSpeed-(?:MM|LLM).*clone")

            for slug in TRAINING_PAGE_CONTRACTS:
                html = (output / slug).read_text(encoding="utf-8")
                self.assertIn('class="rail-card evidence-card"', html)
                self.assertIn(TARGET_FIXED_PREFIX, html)

    def test_foundation_archive_rows_use_project_display_names(self):
        pages = load_page_catalogs([ROOT / "content/site-foundation.json"])
        source_page = next(
            page for page in pages if page["slug"] == "indexes/source-files.html"
        )
        provenance = next(
            section for section in source_page["sections"]
            if section["id"] == "snapshot-provenance"
        )
        table = next(
            block for block in provenance["blocks"]
            if block["type"] == "table"
        )
        archive_rows = [
            row for row in table["rows"] if row[2] == "codeload archive"
        ]
        self.assertEqual(
            [row[0] for row in archive_rows],
            [
                "MindSpeed-MM (mindspeed-mm-0edd553e)",
                "MindSpeed-LLM (mindspeed-llm-434baff7)",
            ],
        )

    def test_render_separates_sections_for_line_oriented_audits(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            build_site(output, [ROOT / "content/site-foundation.json"])
            html = (output / "indexes/source-files.html").read_text(
                encoding="utf-8"
            )
            self.assertIn(
                '</section>\n<section id="file-filters">', html
            )

    def test_render_separates_index_rows_for_line_oriented_audits(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            build_site(output, [ROOT / "content/site-foundation.json"])
            html = (output / "indexes/symbols-configs.html").read_text(
                encoding="utf-8"
            )
            self.assertRegex(html, r"</tr>\n<tr id=\"entry-[0-9a-f]{16}\">")

    def test_cli_default_catalogs_load_only_approved_existing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = root / "content"
            content.mkdir()
            for name in (
                "site-foundation.json",
                "target-architecture.json",
                "target-training.json",
                "site-architecture.json",
                "site-training.json",
            ):
                (content / name).write_text("{}", encoding="utf-8")
            with patch.object(build_site_cli, "ROOT", root):
                self.assertEqual(
                    build_site_cli.default_catalogs(),
                    [
                        content / "site-foundation.json",
                        content / "target-architecture.json",
                        content / "target-training.json",
                    ],
                )

    def test_foundation_build_is_deterministic_and_has_four_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            pages = build_site(output, [ROOT / "content/site-foundation.json"])
            first = {
                path.relative_to(output).as_posix(): path.read_bytes()
                for path in pages
            }
            pages_again = build_site(
                output, [ROOT / "content/site-foundation.json"]
            )
            second = {
                path.relative_to(output).as_posix(): path.read_bytes()
                for path in pages_again
            }
            self.assertEqual(first, second)
            self.assertEqual(
                set(first),
                {
                    "index.html",
                    "indexes/source-files.html",
                    "indexes/symbols-configs.html",
                    "search.html",
                    "assets/search-index.json",
                },
            )

    def test_generated_shell_escapes_content_and_uses_local_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            build_site(output, [ROOT / "content/site-foundation.json"])
            html = (output / "index.html").read_text(encoding="utf-8")
            for element_id in (
                "chapter-nav",
                "article-content",
                "evidence-rail",
                "toggle-left",
                "toggle-right",
                "site-search",
                "chapter-tree",
                "page-toc",
            ):
                self.assertIn(f'id="{element_id}"', html)
            self.assertNotIn("https://fonts", html)
            self.assertIn('src="assets/app.js"', html)
            self.assertEqual(html.count("<h1>"), 1)
            self.assertTrue(
                all(line == line.rstrip() for line in html.splitlines())
            )

    def test_page_catalog_has_unique_order_slug_and_section_ids(self):
        pages = load_page_catalogs([ROOT / "content/site-foundation.json"])
        self.assertEqual(len({page["slug"] for page in pages}), len(pages))
        self.assertEqual(len({page["order"] for page in pages}), len(pages))
        for page in pages:
            ids = [section["id"] for section in page["sections"]]
            self.assertEqual(len(ids), len(set(ids)))

    def test_inline_search_json_cannot_close_its_script_element(self):
        encoded = script_safe_json(
            [{"title": "</script><img src=x onerror=alert(1)>&"}]
        )
        self.assertNotIn("</script", encoded.lower())
        self.assertIn(r"\u003c/script", encoded)
        self.assertIn(r"\u003e", encoded)
        self.assertIn(r"\u0026", encoded)

    def test_top_level_search_list_serializes_one_safe_object_per_line(self):
        documents = [
            {"title": "MindSpeed-MM", "order": 1},
            {"title": "</script> clone", "order": 2},
        ]
        encoded = script_safe_json(documents)
        self.assertEqual(json.loads(encoded), documents)
        self.assertEqual(
            encoded.splitlines(),
            [
                "[",
                '{"order":1,"title":"MindSpeed-MM"},',
                '{"order":2,"title":"\\u003c/script\\u003e clone"}',
                "]",
            ],
        )
        self.assertNotIn("</script", encoded.lower())

    def test_every_page_search_form_targets_relative_search_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            build_site(output, [ROOT / "content/site-foundation.json"])
            self.assertIn(
                'action="search.html"',
                (output / "index.html").read_text(encoding="utf-8"),
            )
            self.assertIn(
                'action="../search.html"',
                (output / "indexes/source-files.html").read_text(
                    encoding="utf-8"
                ),
            )

    def test_catalog_validator_rejects_unknown_evidence_and_block_field(self):
        data = minimal_catalog(
            block={
                "type": "paragraph",
                "text": "x",
                "state": "verified",
                "evidence_ids": ["MISSING"],
                "raw_html": "<b>x</b>",
            }
        )
        errors = validate_catalogs(data, set())
        self.assertIn(
            "catalog.pages[0].sections[0].blocks[0]: unknown field raw_html",
            errors,
        )
        data = minimal_catalog(
            block={
                "type": "paragraph",
                "text": "x",
                "state": "verified",
                "evidence_ids": ["MISSING"],
            }
        )
        errors = validate_catalogs(data, set())
        self.assertIn(
            "catalog.pages[0]#intro: unknown evidence MISSING", errors
        )

    def test_catalog_validator_is_total_for_malformed_containers_and_union(self):
        malformed = [
            None,
            [],
            {},
            {"schema_version": 1, "pages": None},
            {"schema_version": 1, "pages": [None]},
        ]
        for data in malformed:
            with self.subTest(data=data):
                errors = validate_catalogs(data, set())
                self.assertIsInstance(errors, list)
                self.assertTrue(errors)

        for block in (
            {"type": "unknown"},
            {"type": "paragraph", "text": "x"},
            {
                "type": "table",
                "headers": ["a", "b"],
                "rows": [["only one"]],
            },
        ):
            with self.subTest(block=block):
                errors = validate_catalogs(minimal_catalog(block=block), {"E-1"})
                self.assertTrue(errors)

    def test_relative_href_and_search_anchor_contract(self):
        self.assertEqual(
            relative_href("target/model.html", "search.html"), "../search.html"
        )
        self.assertEqual(
            decision_href(
                "index.html", "research/reference-selection-proposal.md"
            ),
            "../research/reference-selection-proposal.md",
        )
        self.assertEqual(
            decision_href(
                "target/model.html",
                "research/reference-selection-proposal.md",
            ),
            "../../research/reference-selection-proposal.md",
        )
        documents = build_search_documents(
            minimal_catalog()["pages"], fixture_indexes()
        )
        self.assertEqual(
            documents,
            sorted(
                documents,
                key=lambda row: (row["kind"], row["title"], row["href"]),
            ),
        )
        symbol = next(row for row in documents if row["kind"] == "symbol")
        self.assertRegex(
            symbol["href"],
            r"^indexes/symbols-configs\.html#entry-[0-9a-f]{16}$",
        )

    def test_search_metadata_is_complete_without_source_body_or_values(self):
        documents = build_search_documents(
            minimal_catalog()["pages"], fixture_indexes()
        )
        self.assertEqual(
            {doc["kind"] for doc in documents},
            {"page", "file", "symbol", "config"},
        )
        for document in documents:
            self.assertNotIn("body", document)
            self.assertNotIn("source", document)
            self.assertNotIn("value", document)
        self.assertIn("pkg/a.py", next(d for d in documents if d["kind"] == "file")["searchable"])
        self.assertIn("c", next(d for d in documents if d["kind"] == "symbol")["searchable"])
        self.assertIn("flag", next(d for d in documents if d["kind"] == "config")["searchable"])

    def test_render_resolves_evidence_decisions_and_escapes_all_values(self):
        page = minimal_catalog(text='<img src=x onerror="boom">')["pages"][0]
        html = render_page(
            page,
            [page],
            fixture_evidence(
                decision_refs=("research/reference-selection-proposal.md",)
            ),
            [],
        )
        self.assertIn('id="chapter-nav"', html)
        self.assertIn('id="article-content"', html)
        self.assertIn('id="evidence-rail"', html)
        self.assertIn(
            'href="../research/reference-selection-proposal.md"', html
        )
        self.assertNotIn("<img src=x", html)
        self.assertIn("&lt;img", html)

    def test_render_rejects_unknown_evidence_unsupported_block_and_bad_rows(self):
        page = minimal_catalog()["pages"][0]
        with self.assertRaisesRegex(
            ValueError, r"page index\.html#intro: unknown evidence E-1"
        ):
            render_page(page, [page], {}, [])

        unsupported = copy.deepcopy(page)
        unsupported["sections"][0]["blocks"] = [{"type": "future"}]
        with self.assertRaisesRegex(ValueError, r"block future: unsupported"):
            render_page(unsupported, [unsupported], fixture_evidence(), [])

        bad_table = copy.deepcopy(page)
        bad_table["sections"][0]["blocks"] = [
            {"type": "table", "headers": ["a", "b"], "rows": [["one"]]}
        ]
        with self.assertRaisesRegex(
            ValueError, r"table intro: row width 1 expected 2"
        ):
            render_page(bad_table, [bad_table], fixture_evidence(), [])

    def test_foundation_content_contract(self):
        pages = load_page_catalogs([ROOT / "content/site-foundation.json"])
        self.assertEqual(len(pages), 4)
        expected_sections = {
            "index.html": {
                "public-scope",
                "learning-path",
                "environment-lanes",
                "phase-boundary",
            },
            "indexes/source-files.html": {
                "snapshot-provenance",
                "file-filters",
                "future-interface",
            },
            "indexes/symbols-configs.html": {
                "symbol-index",
                "config-index",
                "limits",
            },
            "search.html": {
                "search-results",
                "no-script-index",
                "search-scope",
            },
        }
        for page in pages:
            self.assertTrue(page["objectives"])
            self.assertIn(
                "熟悉 PyTorch 单卡张量与训练循环", page["prerequisites"]
            )
            self.assertEqual(
                {section["id"] for section in page["sections"]},
                expected_sections[page["slug"]],
            )

        homepage = next(page for page in pages if page["slug"] == "index.html")
        homepage_json = json.dumps(homepage, ensure_ascii=False)
        self.assertIn("本阶段没有运行 Qwen3-TTS 训练。", homepage_json)
        self.assertIn("CANN 8.5.2 兼容性：unknown，待真机验证。", homepage_json)
        for package in (
            "目标源码架构走读",
            "MindSpeed-MM 训练栈映射",
            "分布式与性能契约",
            "环境与兼容性验证",
            "单机到规模化 SFT 教程",
        ):
            self.assertIn(package, homepage_json)

    def test_architecture_catalog_covers_required_target_symbols(self):
        pages = load_page_catalogs(TARGET_CATALOGS)
        self.assertEqual(len(pages), 9)
        targets = [page for page in pages if page["group"] == "target-architecture"]
        self.assertEqual(
            [(page["order"], page["slug"], page["title"]) for page in targets],
            [
                (
                    contract["order"],
                    slug,
                    contract["title"],
                )
                for slug, contract in TARGET_PAGE_CONTRACTS.items()
            ],
        )

        for page in targets:
            with self.subTest(slug=page["slug"]):
                contract = TARGET_PAGE_CONTRACTS[page["slug"]]
                sections = {
                    section["id"]: section for section in page["sections"]
                }
                self.assertEqual(set(sections), set(contract["sections"]))
                self.assertTrue(page["objectives"])
                self.assertEqual(
                    page["prerequisites"],
                    ["熟悉 PyTorch 单卡张量与自回归生成"],
                )

                for section_id, expected_evidence in contract["sections"].items():
                    actual_evidence = set()
                    for block in sections[section_id]["blocks"]:
                        actual_evidence.update(block.get("evidence_ids", []))
                        for item in block.get("items", []):
                            actual_evidence.update(item.get("evidence_ids", []))
                    self.assertTrue(
                        expected_evidence <= actual_evidence,
                        f"{page['slug']}#{section_id}: "
                        f"missing {expected_evidence - actual_evidence}",
                    )

                chains = [
                    block
                    for section in page["sections"]
                    for block in section["blocks"]
                    if block["type"] == "call_chain"
                ]
                self.assertTrue(chains)
                self.assertEqual(
                    [
                        (item["label"], item["path"], item["symbol"])
                        for item in chains[0]["items"]
                    ],
                    contract["call_chain"],
                )
                source_tables = [
                    block
                    for section in page["sections"]
                    for block in section["blocks"]
                    if block["type"] == "table"
                    and "源码路径" in block["headers"]
                    and block["rows"]
                ]
                self.assertTrue(source_tables)
                source_path_index = next(
                    table["headers"].index("源码路径")
                    for table in source_tables
                )
                actual_source_paths = {
                    row[source_path_index]
                    for table in source_tables
                    for row in table["rows"]
                }
                self.assertTrue(
                    contract["source_paths"] <= actual_source_paths,
                    f"{page['slug']}: missing source paths "
                    f"{contract['source_paths'] - actual_source_paths}",
                )
                self.assertTrue(sections[contract["boundary"]]["blocks"])

        serialized = json.dumps(targets, ensure_ascii=False)
        for symbol in (
            "Qwen3TTSModel.from_pretrained",
            "Qwen3TTSForConditionalGeneration",
            "Qwen3TTSTalkerForConditionalGeneration",
            "forward_sub_talker_finetune",
            "Qwen3TTSSpeakerEncoder",
            "Qwen3TTSTokenizerV2Model",
            "Qwen3TTSTokenizerV1Model",
            "Qwen3TTSProcessor",
        ):
            self.assertIn(symbol, serialized)
        self.assertIn("已证实：静态依赖与源码路径", serialized)
        self.assertIn("待真机验证：公开可执行性 unknown", serialized)
        self.assertIn("24000/1920=12.5 FPS", serialized)
        self.assertIn("推断", serialized)
        self.assertIn("sdist", serialized)
        self.assertIn("不等于源码仓中不存在 examples/finetuning", serialized)
        self.assertIn("codec-0", serialized)
        self.assertIn("num_code_groups - 1", serialized)
        self.assertIn("类默认值为 32", serialized)
        self.assertIn("实际发布 checkpoint 配置 pending", serialized)
        self.assertNotIn("15 个残差码本组", serialized)
        self.assertIn("(T,16)", serialized)
        self.assertIn("x-vector-only", serialized)
        self.assertIn("ICL text+audio", serialized)
        self.assertNotRegex(serialized, r"CANN 8\.5\.2.*(?:兼容|支持|跑通)")
        self.assertNotRegex(serialized, r"(?:Ascend|昇腾).*(?:兼容|支持|跑通)")

    def test_architecture_call_flows_follow_fixed_source_branches(self):
        pages = {
            page["slug"]: page for page in load_page_catalogs(TARGET_CATALOGS)
        }

        def section(slug, section_id):
            return next(
                item
                for item in pages[slug]["sections"]
                if item["id"] == section_id
            )

        def chains(slug, section_id):
            return [
                block
                for block in section(slug, section_id)["blocks"]
                if block["type"] == "call_chain"
            ]

        def symbols(chain):
            return [item["symbol"] for item in chain["items"]]

        package = "target/package-inference-api.html"
        self.assertTrue(chains(package, "base-api"))
        self.assertEqual(
            symbols(chains(package, "base-api")[0]),
            [
                "Qwen3TTSModel.create_voice_clone_prompt",
                "Qwen3TTSModel.generate_voice_clone",
                "Qwen3TTSForConditionalGeneration.generate",
                "Qwen3TTSTokenizer.decode",
            ],
        )
        self.assertEqual(
            symbols(chains(package, "voice-design-api")[0]),
            [
                "Qwen3TTSModel.generate_voice_design",
                "Qwen3TTSForConditionalGeneration.generate",
                "Qwen3TTSTokenizer.decode",
            ],
        )
        self.assertEqual(
            symbols(chains(package, "custom-api")[0]),
            [
                "Qwen3TTSModel.generate_custom_voice",
                "Qwen3TTSForConditionalGeneration.generate",
                "Qwen3TTSTokenizer.decode",
            ],
        )

        model = "target/model-architecture.html"
        model_chains = chains(model, "generation-flow")
        self.assertEqual(len(model_chains), 2)
        self.assertEqual(
            symbols(model_chains[1]),
            [
                "Qwen3TTSModel.generate_voice_clone / generate_voice_design / generate_custom_voice",
                "Qwen3TTSForConditionalGeneration.generate",
                "self.talker.generate / Qwen3TTSTalkerForConditionalGeneration.forward",
                "self.code_predictor.generate",
                "Qwen3TTSTokenizer.decode / self.model.speech_tokenizer.decode",
            ],
        )
        inference_json = json.dumps(model_chains[1], ensure_ascii=False)
        self.assertNotIn("forward_sub_talker_finetune", inference_json)
        self.assertIn(
            "forward_sub_talker_finetune",
            json.dumps(section(model, "code-predictor"), ensure_ascii=False),
        )
        self.assertIn(
            "forward_finetune",
            json.dumps(section(model, "code-predictor"), ensure_ascii=False),
        )
        speaker_json = json.dumps(
            section(model, "speaker-encoder"), ensure_ascii=False
        )
        self.assertIn("TGT-CONFIG-001", speaker_json)

        tokenizer_12 = "target/tokenizer-12hz.html"
        self.assertTrue(chains(tokenizer_12, "decode-contract"))
        encode_12 = chains(tokenizer_12, "encode-contract")[0]
        self.assertEqual(
            symbols(encode_12),
            ["Qwen3TTSTokenizerV2Model.encode", "self.encoder.encode"],
        )
        self.assertNotIn(
            "SplitResidualVectorQuantizer",
            json.dumps(encode_12, ensure_ascii=False),
        )
        self.assertEqual(
            symbols(chains(tokenizer_12, "decode-contract")[0]),
            [
                "Qwen3TTSTokenizerV2Model.decode",
                "Qwen3TTSTokenizerV2Decoder.chunked_decode",
                "Qwen3TTSTokenizerV2Decoder.forward",
                "SplitResidualVectorQuantizer.decode",
            ],
        )
        decode_shape = next(
            block
            for block in section(tokenizer_12, "decode-contract")["blocks"]
            if block["type"] == "paragraph" and "(B,T,16)" in block["text"]
        )
        self.assertEqual(decode_shape["state"], "inference")
        self.assertEqual(
            decode_shape["evidence_ids"],
            ["TGT-TOK12-001", "TGT-TOK12-002"],
        )

        tokenizer_25 = "target/tokenizer-25hz.html"
        self.assertTrue(chains(tokenizer_25, "vq-core"))
        self.assertTrue(chains(tokenizer_25, "dit-bigvgan"))
        self.assertEqual(
            symbols(chains(tokenizer_25, "encoder-vq")[0]),
            [
                "Qwen3TTSTokenizerV1Model.encode",
                "Qwen3TTSTokenizerV1Encoder.quantize_speech",
                "Qwen3TTSTokenizerV1Encoder.speech2mel",
                "Qwen3TTSTokenizerV1Encoder.mel2code",
            ],
        )
        self.assertEqual(
            [symbols(chain) for chain in chains(tokenizer_25, "vq-core")],
            [
                ["DistributedGroupResidualVectorQuantization.encode"],
                ["DistributedGroupResidualVectorQuantization.decode"],
            ],
        )
        self.assertEqual(
            symbols(chains(tokenizer_25, "dit-bigvgan")[0]),
            [
                "Qwen3TTSTokenizerV1Model.decode",
                "Qwen3TTSTokenizerV1Decoder.forward",
                "Qwen3TTSTokenizerV1DecoderDiTModel.sample",
                "Qwen3TTSTokenizerV1DecoderBigVGANModel.forward",
            ],
        )

        processor = "target/processor-contracts.html"
        self.assertTrue(chains(processor, "text-contract"))
        self.assertTrue(chains(processor, "prompt-contract"))
        text_flow = chains(processor, "text-contract")[0]
        audio_flows = chains(processor, "audio-wrapper")
        prompt_flow = chains(processor, "prompt-contract")[0]
        self.assertEqual(
            symbols(text_flow),
            [
                "Qwen3TTSProcessor.apply_chat_template",
                "Qwen3TTSProcessor.__call__",
                "BatchFeature",
            ],
        )
        self.assertEqual(len(audio_flows), 2)
        self.assertEqual(
            symbols(audio_flows[0]),
            [
                "Qwen3TTSTokenizer.encode",
                "Qwen3TTSTokenizer._normalize_audio_inputs",
                "self.feature_extractor",
                "self.model.encode (V1/V2 dispatch)",
            ],
        )
        self.assertEqual(
            symbols(audio_flows[1]),
            [
                "Qwen3TTSTokenizer.decode",
                "model_type branch",
                "self.model.decode (V1/V2 dispatch)",
                "self.model.get_output_sample_rate",
            ],
        )
        self.assertNotIn(
            "Qwen3TTSProcessor",
            json.dumps(audio_flows, ensure_ascii=False),
        )
        self.assertEqual(
            symbols(prompt_flow),
            [
                "Qwen3TTSModel.create_voice_clone_prompt",
                "x_vector_only_mode / icl_mode",
                "Qwen3TTSModel.generate_voice_clone",
            ],
        )
        prompt_json = json.dumps(
            section(processor, "prompt-contract"), ensure_ascii=False
        )
        self.assertIn("TGT-API-002", prompt_json)
        shape = next(
            block
            for block in section(processor, "shape-contract")["blocks"]
            if block["type"] == "paragraph"
        )
        self.assertEqual(shape["state"], "inference")
        self.assertIn("TGT-TOK12-002", shape["evidence_ids"])

    def test_generated_architecture_site_preserves_navigation_search_and_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            built = build_site(output, TARGET_CATALOGS)
            html_paths = [path for path in built if path.suffix == ".html"]
            self.assertEqual(len(html_paths), 9)

            pages = load_page_catalogs(TARGET_CATALOGS)
            indexes = load_all_indexes()
            expected_document_count = len(pages) + sum(
                len(index[dataset])
                for index in indexes.values()
                for dataset in ("files", "symbols", "configs")
            )
            self.assertEqual(expected_document_count, 47_500)
            external = json.loads(
                (output / "assets/search-index.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(len(external), expected_document_count)

            search_html = (output / "search.html").read_text(encoding="utf-8")
            match = re.search(
                r'<script id="search-data" type="application/json">(.*?)</script>',
                search_html,
                re.DOTALL,
            )
            self.assertIsNotNone(match)
            self.assertEqual(json.loads(match.group(1)), external)

            expected_nav = [
                (page["order"], page["title"]) for page in pages
            ]
            for path in html_paths:
                html = path.read_text(encoding="utf-8")
                self.assertEqual(html.count("<h1>"), 1)
                nav = re.search(
                    r'<ul id="chapter-tree" class="chapter-tree">(.*?)</ul>',
                    html,
                    re.DOTALL,
                )
                self.assertIsNotNone(nav)
                self.assertEqual(
                    [
                        (int(order), title)
                        for order, title in re.findall(
                            r">(\d+) · ([^<]+)</a>", nav.group(1)
                        )
                    ],
                    expected_nav,
                )

                parser = LinkParser()
                parser.feed(html)
                self.assertEqual(len(parser.ids), len(set(parser.ids)))
                for href in parser.links:
                    if href.startswith("#"):
                        self.assertIn(
                            href[1:],
                            parser.ids,
                            f"{path.relative_to(output)} -> {href}",
                        )
                        continue
                    if href.startswith(("http://", "https://", "mailto:")):
                        continue
                    target_text, _, fragment = href.partition("#")
                    target_text = target_text.split("?", 1)[0]
                    if target_text.endswith(".html"):
                        target = (path.parent / target_text).resolve()
                        self.assertTrue(
                            target.is_file(),
                            f"{path.relative_to(output)} -> {href}",
                        )
                        if fragment:
                            target_parser = LinkParser()
                            target_parser.feed(
                                target.read_text(encoding="utf-8")
                            )
                            self.assertIn(
                                fragment,
                                target_parser.ids,
                                f"{path.relative_to(output)} -> {href}",
                            )

            cross_page_fragments = [
                document["href"]
                for document in external
                if "#" in document["href"]
                and document["href"].split("#", 1)[0].endswith(".html")
            ]
            self.assertTrue(cross_page_fragments)
            fragment_cache = {}
            for href in cross_page_fragments:
                target_text, fragment = href.split("#", 1)
                if target_text not in fragment_cache:
                    target_parser = LinkParser()
                    target_parser.feed(
                        (output / target_text).read_text(encoding="utf-8")
                    )
                    fragment_cache[target_text] = set(target_parser.ids)
                self.assertIn(fragment, fragment_cache[target_text])

            for slug in TARGET_PAGE_CONTRACTS:
                html = (output / slug).read_text(encoding="utf-8")
                self.assertIn(TARGET_FIXED_PREFIX, html)
                self.assertNotIn("github.com/QwenLM/Qwen3-TTS/blob/main/", html)
                self.assertIn('class="rail-card evidence-card"', html)
                self.assertGreaterEqual(html.count('data-state="'), 2)
                self.assertGreaterEqual(
                    html.count('data-evidence-state="'), 2
                )

    def test_search_page_inline_documents_match_file_and_runtime_is_local(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            build_site(output, [ROOT / "content/site-foundation.json"])
            html = (output / "search.html").read_text(encoding="utf-8")
            match = re.search(
                r'<script id="search-data" type="application/json">(.*?)</script>',
                html,
                re.DOTALL,
            )
            self.assertIsNotNone(match)
            inline = json.loads(match.group(1))
            external = json.loads(
                (output / "assets/search-index.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(inline, external)
            metadata = [doc for doc in inline if doc["kind"] != "page"]
            expected_snapshots = {
                "qwen3-tts-022e286b",
                "mindspeed-mm-0edd553e",
                "mindspeed-llm-434baff7",
                "moss-tts-ad99ec5f",
            }
            self.assertEqual(
                {doc["summary"] for doc in metadata}, expected_snapshots
            )
            for snapshot_id in expected_snapshots:
                self.assertEqual(
                    {
                        doc["kind"]
                        for doc in metadata
                        if doc["summary"] == snapshot_id
                    },
                    {"file", "symbol", "config"},
                )
            parser = LinkParser()
            parser.feed(html)
            self.assertEqual(len(parser.ids), len(set(parser.ids)))
            self.assertIn('class="search-results"', html)
            self.assertIn('id="search-results-status"', html)
            self.assertIn('id="no-script-index"', html)
            self.assertNotRegex(
                html,
                r'<(?:script|link)[^>]+(?:src|href)="https?://',
            )

            app = (ROOT / "site/assets/app.js").read_text(encoding="utf-8")
            self.assertNotIn("fetch(", app)
            self.assertIn("replaceChildren", app)
            self.assertIn("textContent", app)
            self.assertIn("replaceState", app)

    def test_generated_local_links_resolve_within_current_foundation(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            built = build_site(output, [ROOT / "content/site-foundation.json"])
            html_paths = [path for path in built if path.suffix == ".html"]
            for path in html_paths:
                parser = LinkParser()
                parser.feed(path.read_text(encoding="utf-8"))
                for href in parser.links:
                    if href.startswith(("http://", "https://", "mailto:", "#")):
                        continue
                    target_text = href.split("#", 1)[0].split("?", 1)[0]
                    if not target_text.endswith(".html"):
                        continue
                    target = (path.parent / target_text).resolve()
                    self.assertTrue(
                        target.is_file(),
                        f"{path.relative_to(output)} -> {href}",
                    )

    def test_css_tokens_and_breakpoints_are_preserved(self):
        theme = (ROOT / "site/assets/theme.css").read_text(encoding="utf-8")
        layout = (ROOT / "site/assets/layout.css").read_text(encoding="utf-8")
        for declaration in (
            "--canvas: #f7f1e7",
            "--header: #e8ddcd",
            "--left-bg: #eee5d8",
            "--article-bg: #fcf9f3",
            "--right-bg: #f1e8dc",
            "--ink: #2b251f",
            "--accent: #934735",
            "--code-bg: #22211e",
        ):
            self.assertIn(declaration, theme)
        self.assertIn("@media (max-width: 1199px)", layout)
        self.assertIn("@media (max-width: 720px)", layout)
        self.assertIn("@media (max-width: 390px)", layout)
        self.assertIn(".status-grid", theme)
        self.assertIn(".contract-table", theme)
        self.assertIn(".index-table", theme)
        self.assertIn(".search-results", theme)
        self.assertIn(".evidence-state", theme)


if __name__ == "__main__":
    unittest.main()
