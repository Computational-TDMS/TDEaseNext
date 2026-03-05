#!/bin/bash
# 修复节点类型判断和数据源解析逻辑

echo "Applying node type fix..."

# 备份原文件
cp D:/Projects/TDEase-Backend/TDEase-FrontEnd/src/components/workflow/VueFlowCanvas.vue D:/Projects/TDEase-Backend/TDEase-FrontEnd/src/components/workflow/VueFlowCanvas.vue.backup2
cp D:/Projects/TDEase-Backend/TDEase-FrontEnd/src/services/workflow-connector.ts D:/Projects/TDEase-Backend/TDEase-FrontEnd/src/services/workflow-connector.ts.backup2

# 修复 VueFlowCanvas.vue 的节点类型判断逻辑
cd D:/Projects/TDEase-Backend

cat > /tmp/fix_nodes.txt << 'EOF'
  // 从 store 获取数据并转换为 Vue Flow 格式
  const nodes = computed<Node<any, any, string>[]>(() => workflowStore.nodes.map((node) => {
    // Determine node type based on executionMode
    let nodeType = node.type

    // Debug logging
    console.log(`[VueFlowCanvas] Processing node ${node.id}:`, {
      type: node.type,
      executionMode: node.executionMode,
      label: node.displayProperties?.label || node.data?.label
    })

    // Priority 1: Check executionMode first (most important)
    if (node.executionMode === 'interactive') {
      nodeType = 'interactive'
      console.log(`[VueFlowCanvas] Node ${node.id} is interactive (by executionMode)`)
    }
    // Priority 2: Check for specific node types
    else if (node.type === 'filter') {
      nodeType = 'filter'
    }
    // Priority 3: Check for other known types
    else if (['custom', 'input', 'process', 'output', 'tool'].includes(node.type)) {
      nodeType = node.type
    }
    // Default to tool node
    else {
      nodeType = 'tool'
    }

    console.log(`[VueFlowCanvas] Node ${node.id} resolved to type: ${nodeType}`)
EOF

# 使用 Python 来做精确的文件替换
python3 << 'PYTHON_SCRIPT'
import re

# 读取 VueFlowCanvas.vue
with open('D:/Projects/TDEase-Backend/TDEase-FrontEnd/src/components/workflow/VueFlowCanvas.vue', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换节点类型判断逻辑
old_pattern = r'  const nodes = computed<Node<any, any, string>\[\]>\(\) => workflowStore\.nodes\.map\(\(node\) => \{.*?\n    \}.*?\n    \}.*?\n    \}.*?\n    \}.*?\n  \}\)\)'

new_code = '''  const nodes = computed<Node<any, any, string>[]>(() => workflowStore.nodes.map((node) => {
    // Determine node type based on executionMode
    let nodeType = node.type

    // Debug logging
    console.log(`[VueFlowCanvas] Processing node ${node.id}:`, {
      type: node.type,
      executionMode: node.executionMode,
      label: node.displayProperties?.label || node.data?.label
    })

    // Priority 1: Check executionMode first (most important)
    if (node.executionMode === 'interactive') {
      nodeType = 'interactive'
      console.log(`[VueFlowCanvas] Node ${node.id} is interactive (by executionMode)`)
    }
    // Priority 2: Check for specific node types
    else if (node.type === 'filter') {
      nodeType = 'filter'
    }
    // Priority 3: Check for other known types
    else if (['custom', 'input', 'process', 'output', 'tool'].includes(node.type)) {
      nodeType = node.type
    }
    // Default to tool node
    else {
      nodeType = 'tool'
    }

    console.log(`[VueFlowCanvas] Node ${node.id} resolved to type: ${nodeType}`)

    const resolvedToolId =
      (node as any).nodeConfig?.toolId ||
      (node as any).data?.toolId ||
      (node as any).data?.type ||
      (node.type !== 'tool' ? node.type : null)

    return {
      id: node.id,
      type: nodeType,
      position: node.position,
      data: {
        nodeId: node.id,
        label: node.displayProperties?.label || node.data?.label || node.type,
        color: node.displayProperties?.color || node.data?.color || '#409eff',
        icon: node.displayProperties?.icon,
        executionMode: node.executionMode,
        toolId: typeof resolvedToolId === 'string' ? resolvedToolId : node.type,
        visualizationConfig: node.visualizationConfig,
        nodeConfig: {
          inputs: node.inputs.map((p) => ({
            id: p.id,
            name: p.name,
            type: (p as any).dataType || (p as any).type || 'file',
            required: (p as any).required === true,
            accept: Array.isArray((p as any).accept) ? (p as any).accept : undefined,
            dataType: (p as any).dataType,
            portKind: (p as any).portKind,
            semanticType: (p as any).semanticType
          })),
          outputs: node.outputs.map((p) => ({
            id: p.id,
            name: p.name,
            type: (p as any).dataType || (p as any).type || 'file',
            pattern: (p as any).pattern,
            provides: Array.isArray((p as any).provides) ? (p as any).provides : undefined,
            dataType: (p as any).dataType,
            portKind: (p as any).portKind,
            semanticType: (p as any).semanticType
          }))
        }
      },
      style: {
        backgroundColor: 'transparent',
        border: 'none',
        padding: '0',
        width: 'auto',
        height: 'auto'
      },
      draggable: true,
      selectable: true
    }
  }))'''

# 简单的替换（找到开始和结束标记）
start_marker = '  const nodes = computed<Node<any, any, string>[]>(() => workflowStore.nodes.map((node) => {'
end_marker = '  }))'

start_idx = content.find(start_marker)
if start_idx != -1:
    # 找到对应的结束标记（从 start_idx 开始查找）
    end_idx = content.find(end_marker, start_idx)
    if end_idx != -1:
        # 替换这部分
        new_content = content[:start_idx] + new_code + content[end_idx + len(end_marker):]

        with open('D:/Projects/TDEase-Backend/TDEase-FrontEnd/src/components/workflow/VueFlowCanvas.vue', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✓ Fixed VueFlowCanvas.vue")
    else:
        print("✗ End marker not found in VueFlowCanvas.vue")
else:
    print("✗ Start marker not found in VueFlowCanvas.vue")

PYTHON_SCRIPT

echo "Fix applied! Please restart frontend to see changes."
