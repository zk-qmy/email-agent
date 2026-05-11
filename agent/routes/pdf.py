import os
import json
import tempfile
from typing import Optional
from pydantic import BaseModel
from fastapi import UploadFile, File, Form, HTTPException


class PdfFormField(BaseModel):
    name: str
    type: str
    required: bool
    value: Optional[str] = None


class PdfParseResponse(BaseModel):
    text: str
    page_count: int
    form_fields: list[PdfFormField] = []


class ValidatePdfRequest(BaseModel):
    text: str
    user_role: str


class ValidatePdfResponse(BaseModel):
    required_fields: list[str]
    optional_fields: list[str]
    not_user_fields: list[str]
    missing_fields: list[str]
    message_to_user: str


_FIELD_TYPE_MAP = {
    "Tx": "text",
    "Btn": "checkbox",
    "Ch": "choice",
    "Sig": "signature",
}


def _extract_form_fields(pdf) -> list[dict]:
    form_fields = []
    try:
        acroform = pdf.doc.catalog.get("AcroForm")
        if acroform is None:
            return form_fields

        from pdfplumber.utils.pdfinternals import resolve_and_decode, resolve

        resolved_acro = resolve(acroform)
        if resolved_acro is None:
            return form_fields

        raw_fields = resolved_acro.get("Fields")
        if raw_fields is None:
            return form_fields

        fields = resolve(raw_fields)
        if not fields:
            return form_fields

        def _parse(field, prefix=None):
            resolved = field.resolve()
            raw_name = resolved.get("T", "")
            field_name = resolve_and_decode(raw_name) if raw_name else ""
            full_name = ".".join(filter(None, [prefix, field_name]))

            if "Kids" in resolved:
                for kid in resolved["Kids"]:
                    _parse(kid, prefix=full_name)

            if "T" in resolved or "TU" in resolved:
                ft_raw = resolved.get("FT")
                ft_str = resolve_and_decode(ft_raw) if ft_raw else None

                ff_raw = resolved.get("Ff")
                ff = resolve_and_decode(ff_raw) if ff_raw else 0

                v_raw = resolved.get("V")
                value = resolve_and_decode(v_raw) if v_raw else None
                if value is not None and not isinstance(value, str):
                    value = str(value)

                form_fields.append({
                    "name": field_name,
                    "type": _FIELD_TYPE_MAP.get(str(ft_str), "unknown") if ft_str else "unknown",
                    "required": bool(ff & 2) if isinstance(ff, int) else False,
                    "value": value,
                })

        for field in fields:
            _parse(field)

    except Exception:
        pass

    return form_fields


async def parse_pdf_file(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        import pdfplumber
        with pdfplumber.open(tmp_path) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
            full_text = " ".join(" ".join(pages).split())
            page_count = len(pdf.pages)
            form_fields = _extract_form_fields(pdf)

        os.unlink(tmp_path)
        return PdfParseResponse(text=full_text, page_count=page_count, form_fields=form_fields)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {str(e)}")


async def validate_pdf_content(request: ValidatePdfRequest):
    from src.agent.tools.email_mining_tools import validate_pdf as _validate_pdf

    try:
        result = _validate_pdf.invoke({"file_content": request.text, "user_role": request.user_role})
        if "error" in result:
            raise HTTPException(status_code=502, detail=result.get("raw_output", result["error"]))
        return ValidatePdfResponse(**result)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid response from validation service")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


async def validate_pdf_upload(
    file: UploadFile = File(...),
    user_role: str = Form(...),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        import pdfplumber
        with pdfplumber.open(tmp_path) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
            full_text = " ".join(" ".join(pages).split())
            form_fields = _extract_form_fields(pdf)

        os.unlink(tmp_path)

        filled = [f for f in form_fields if f.get("value")]
        if filled:
            lines = "\n".join(f"  - {f['name']}: {f['value']}" for f in filled)
            full_text = f"{full_text}\n\n--- Filled Form Fields ---\n{lines}"

        from src.agent.tools.email_mining_tools import validate_pdf as _validate_pdf
        result = _validate_pdf.invoke({"file_content": full_text, "user_role": user_role})
        if "error" in result:
            raise HTTPException(status_code=502, detail=result.get("raw_output", result["error"]))
        return ValidatePdfResponse(**result)

    except HTTPException:
        raise
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid response from validation service")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")
