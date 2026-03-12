import os
import shutil
import subprocess
import tempfile
import zipfile
from xml.sax.saxutils import escape

from fastapi import HTTPException, status

from core import config


class FormsServices:
    _FORM_01_TEMPLATE = "FORM_01_Informativa_PMI_partecipanti.docx"

    def render_form_01_pdf(self, data: dict[str, str]) -> bytes:
        template_path = os.path.join(
            config.APIConfig.BASE_DIR,
            "templates",
            self._FORM_01_TEMPLATE,
        )

        if not os.path.exists(template_path):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Template not found: {self._FORM_01_TEMPLATE}",
            )

        office_binary =  shutil.which("libreoffice") or shutil.which("soffice")
        if not office_binary:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="soffice/libreoffice binary not available on server",
            )

        safe_data = {self._normalize_key(key): str(value) for key, value in data.items()}

        with tempfile.TemporaryDirectory() as temp_dir:
            rendered_docx_path = os.path.join(temp_dir, "FORM_01_Informativa_PMI_partecipanti.docx")
            rendered_pdf_path = os.path.join(temp_dir, "FORM_01_Informativa_PMI_partecipanti.pdf")
            shutil.copyfile(template_path, rendered_docx_path)

            self._replace_docx_placeholders(rendered_docx_path, safe_data)

            result = subprocess.run(
                [
                    office_binary,
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    temp_dir,
                    rendered_docx_path,
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=(
                        "Soffice conversion failed. "
                        f"stdout='{result.stdout.strip()}' stderr='{result.stderr.strip()}'"
                    ),
                )

            if not os.path.exists(rendered_pdf_path):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=(
                        "Soffice conversion failed: output file not produced. "
                        f"stdout='{result.stdout.strip()}' stderr='{result.stderr.strip()}' "
                        f"outdir_files='{sorted(os.listdir(temp_dir))}'"
                    ),
                )

            with open(rendered_pdf_path, "rb") as pdf_file:
                return pdf_file.read()

    def _normalize_key(self, key: str) -> str:
        normalized = key.strip()
        if normalized.startswith("{{") and normalized.endswith("}}"):
            return normalized[2:-2].strip()
        return normalized

    def _replace_docx_placeholders(self, docx_path: str, data: dict[str, str]) -> None:
        temp_docx_path = f"{docx_path}.tmp"

        with zipfile.ZipFile(docx_path, "r") as source_zip:
            with zipfile.ZipFile(temp_docx_path, "w") as target_zip:
                for zip_info in source_zip.infolist():
                    content = source_zip.read(zip_info.filename)

                    if zip_info.filename.endswith(".xml"):
                        xml_text = content.decode("utf-8")
                        for key, value in data.items():
                            xml_text = xml_text.replace(f"{{{{{key}}}}}", escape(value))
                        content = xml_text.encode("utf-8")

                    target_zip.writestr(zip_info, content)

        os.replace(temp_docx_path, docx_path)
