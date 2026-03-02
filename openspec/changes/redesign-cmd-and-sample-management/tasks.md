## 1. Tool Definition Schema 迁移

- [x] 1.1 定义新的 Tool Definition JSON Schema（参照 design.md D1），创建 `config/tool-schema.json` 作为校验模板
- [x] 1.2 迁移 `config/tools/topfd.json` 到新 Schema（ports.inputs 加 positional/positionalOrder，parameters 替代 param_mapping，output 替代 output_flag_supported 等散落字段）
- [x] 1.3 迁移 `config/tools/toppic.json` 到新 Schema
- [x] 1.4 迁移 `config/tools/msconvert.json` 到新 Schema
- [x] 1.5 迁移 `config/tools/data_loader.json` 到新 Schema
- [x] 1.6 迁移 `config/tools/fasta_loader.json` 到新 Schema
- [x] 1.7 更新 `app/services/tool_registry.py`：仅支持新 Schema，完全移除向后兼容代码

## 2. CommandBuilder 重写

- [x] 2.1 创建 `app/core/executor/command_pipeline.py`，实现 Pipeline 模式的命令构建（filter → executable → output-flag → param-flags → positional-args 五步）
- [x] 2.2 实现 Step 1: 参数过滤函数，统一移除 null/empty/"none" 值（替代散落在 normalizer、前端、旧 command_builder 中的多处过滤）
- [x] 2.3 实现 Step 2: 根据 executionMode 和 command 字段解析可执行命令前缀（native → 直接路径，script → interpreter + path，支持 uv）
- [x] 2.4 实现 Step 3: 根据 output.flagSupported/flag/flagValue 决定是否添加输出路径
- [x] 2.5 实现 Step 4: 遍历 parameters，按 type (value/boolean/choice) 生成 flag 参数
- [x] 2.6 实现 Step 5: 从 ports.inputs 中提取 positional=true 的端口，按 positionalOrder 排列位置参数
- [x] 2.7 实现 shell quoting 逻辑（Windows 双引号 / Unix shlex.quote）
- [x] 2.8 将 `app/core/executor/local.py` 中的 CommandBuilder 调用替换为新的 command_pipeline
- [x] 2.9 移除旧 `command_builder.py`（完全去除向后兼容）

## 3. Sample Table 与 SampleResolver (UPDATED per implement-workspace-hierarchy)

**NOTE**: Tasks 3.1-3.5 marked as COMPLETED because `implement-workspace-hierarchy` already implemented sample management via `samples.json` and `UnifiedWorkspaceManager`. Remaining tasks focus on integration.

- [x] 3.1 ✓ COMPLETED: Sample structure exists in `samples.json` via UnifiedWorkspaceManager (implement-workspace-hierarchy)
- [x] 3.2 ✓ COMPLETED: Sample context loading via `UnifiedWorkspaceManager.get_sample_context()` (implement-workspace-hierarchy)
- [x] 3.3 ✓ COMPLETED: Placeholder resolution with auto-derivation in `_build_sample_context()` (implement-workspace-hierarchy)
- [x] 3.4 ✓ COMPLETED: Backward compatibility via samples.json structured data (implement-workspace-hierarchy)
- [x] 3.5 ✓ COMPLETED: Fallback derivation removed - UnifiedWorkspaceManager handles this (implement-workspace-hierarchy)
- [x] 3.6 更新 `app/api/workflow.py`：使用 `UnifiedWorkspaceManager.get_sample_context()` 替代 `_extract_sample_ctx_from_workflow`
- [ ] 3.7 验证 `app/services/workflow_service.py` 中的 `_resolve_output_paths` 和 `_resolve_input_paths` 使用新的占位符验证（已在 implement-workspace-hierarchy Phase 2 实现）

## 4. WorkflowNormalizer 调整

- [x] 4.1 移除 `src/workflow/normalizer.py` 中的 `_filter_empty_params`（参数过滤统一到 CommandBuilder Pipeline Step 1）
- [ ] 4.2 在 normalizer 中保留 `sample_table` 字段的传递（metadata 归一化时保留 sample_table）
- [ ] 4.3 更新 normalizer 的 handle 归一化逻辑，保留 `input-`/`output-` 前缀语义信息而非全部去除

## 5. 前端适配

- [ ] 5.1 同步更新 `TDEase-FrontEnd/config/tools/*.json` 到新 Schema 格式
- [ ] 5.2 更新 `PropertyPanel.vue`：基于 Tool Definition 的 `parameters` 字段渲染参数表单（支持 value/boolean/choice 类型，group 分组，advanced 折叠）
- [ ] 5.3 更新 `PropertyPanel.vue`：保存时仅序列化用户实际填写的非空值，移除独立的 `filterEmptyParams` 函数
- [ ] 5.4 更新 `workflow.ts`：移除独立的参数过滤逻辑（交由后端 CommandBuilder 统一处理）
- [ ] 5.5 更新前端节点渲染：根据 `ports.inputs` 和 `ports.outputs` 渲染输入/输出端口，支持 positional 标记展示

## 6. 批量执行与 API 调整

- [x] 6.1 重构 `/api/workflows/execute` 端点：使用 `UnifiedWorkspaceManager.get_sample_context()` 加载样品上下文
- [ ] 6.2 简化 `/api/workflows/{id}/execute-batch` 端点：基于 samples.json 遍历执行，复用单样本执行路径
- [ ] 6.3 更新 `tests/test.json`：添加样品上下文，验证新格式

## 7. 可视化节点扩展点（预留）

- [ ] 7.1 在 Tool Definition Schema 中添加 `executionMode: "interactive"` 和 `visualization` 字段定义
- [ ] 7.2 在 FlowEngine 中添加 interactive 节点的 "awaiting_interaction" 状态处理逻辑
- [ ] 7.3 预留数据读取 API 端点骨架：`/api/nodes/{node_id}/data`，用于前端可视化组件读取上游输出

## 8. 验证与清理

- [ ] 8.1 使用更新后的 `tests/test.json` 端到端测试完整工作流（data_loader → msconvert → topfd → toppic）
- [ ] 8.2 验证空参数不再出现在命令行（`-f None` 场景）
- [ ] 8.3 验证 TopPIC/TopFD 不再添加 `-o` 输出路径
- [ ] 8.4 验证 `{fasta_filename}` 占位符正确解析
- [ ] 8.5 验证多样本批量执行正确工作
- [ ] 8.6 移除旧的 `command_builder.py`（在所有验证通过后）
- [ ] 8.7 更新 `docs/关于工作流解析的细节.md` 文档，反映新架构
