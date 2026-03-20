from __future__ import annotations

import re

from toolchain.compiler.loader import ModuleGraph
from toolchain.compiler.semantic_ir import build_semantic_ir

PY_PRIMITIVES = {
    "Int": "int",
    "Float": "float",
    "Decimal": "float",
    "Bool": "bool",
    "String": "str",
    "Bytes": "str",
    "Instant": "str",
    "Duration": "str",
    "Uuid": "str",
    "Email": "str",
    "UserId": "str",
    "TenantId": "str",
    "Principal": "dict[str, object]",
}


def _split_qualified(name: str) -> tuple[str | None, str]:
    if "." in name:
        left, right = name.rsplit(".", 1)
        return left, right
    return None, name


def _py_type(type_name: str, current_module: str) -> str:
    qualifier, bare = _split_qualified(type_name)
    if qualifier is None and bare in PY_PRIMITIVES:
        return PY_PRIMITIVES[bare]
    module_name = qualifier or current_module
    return f"{module_name}_{bare}"


def _extract_path_params(path: str) -> list[str]:
    return re.findall(r"\{([^{}]+)\}", path)


def emit_server_fastapi(module_graph: ModuleGraph) -> str:
    ir = build_semantic_ir(module_graph)
    lines: list[str] = []
    lines.append('from __future__ import annotations')
    lines.append('')
    lines.append('from fastapi import APIRouter, FastAPI')
    lines.append('from pydantic import BaseModel')
    lines.append('')
    lines.append('app = FastAPI(title="Astra Generated Server", version="0.1.0")')
    lines.append('')

    for module_name, module_ir in ir.modules.items():
        for schema in module_ir.schemas:
            class_name = f"{module_name}_{schema.name}"
            lines.append(f'class {class_name}(BaseModel):')
            if schema.fields:
                for field in schema.fields:
                    lines.append(f'    {field.name}: {_py_type(field.type_ref.qualified_name, module_name)}')
            else:
                lines.append('    pass')
            lines.append('')
        for command in module_ir.commands:
            class_name = f"{module_name}_{command.name}"
            lines.append(f'class {class_name}(BaseModel):')
            if command.fields:
                for field in command.fields:
                    lines.append(f'    {field.name}: {_py_type(field.type_ref.qualified_name, module_name)}')
            else:
                lines.append('    pass')
            lines.append('')
        for event in module_ir.events:
            class_name = f"{module_name}_{event.name}"
            lines.append(f'class {class_name}(BaseModel):')
            if event.fields:
                for field in event.fields:
                    lines.append(f'    {field.name}: {_py_type(field.type_ref.qualified_name, module_name)}')
            else:
                lines.append('    pass')
            lines.append('')

    for module_name, module_ir in ir.modules.items():
        query_map = {q.name: q for q in module_ir.queries}
        lines.append(f'{module_name}_router = APIRouter(prefix="", tags=["{module_name}"])')
        lines.append('')
        for api in module_ir.apis:
            for route in api.routes:
                target_module, target_name = _split_qualified(route.target)
                target_module = target_module or module_name
                method = route.method.lower()
                handler_name = f'{module_name}_{api.name}_{method}_{target_name}'.replace('-', '_')
                params = _extract_path_params(route.path)
                signature_parts: list[str] = []
                for p in params:
                    query = query_map.get(target_name) if target_module == module_name else None
                    typ = 'str'
                    if query and query.input_type and p.lower() in {'id', 'userid', 'tenantid'}:
                        typ = _py_type(query.input_type.qualified_name, target_module)
                    signature_parts.append(f'{p}: {typ}')
                response_model = None
                body_part = None
                if route.target_kind == 'command':
                    body_part = f'payload: {target_module}_{target_name}'
                    signature_parts.append(body_part)
                    response_model = 'dict'
                else:
                    query = query_map.get(target_name) if target_module == module_name else None
                    if query and query.output_type:
                        response_model = _py_type(query.output_type.qualified_name, target_module)
                decorator = f'@{module_name}_router.{method}("{route.path}"'
                if response_model:
                    decorator += f', response_model={response_model}'
                decorator += ')'
                lines.append(decorator)
                sig = ', '.join(signature_parts)
                lines.append(f'async def {handler_name}({sig})' + ':')
                if route.target_kind == 'command':
                    lines.append('    return {"status": "accepted", "handled_by": "Astra generated stub"}')
                else:
                    lines.append('    raise NotImplementedError("Implement query handler binding")')
                lines.append('')
        lines.append(f'app.include_router({module_name}_router)')
        lines.append('')

    return '\n'.join(lines).rstrip() + '\n'
