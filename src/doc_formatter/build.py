"""Publish a Word build only after package checks pass."""
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

from .backends.docx import emit, run_tool
from .compiler import parse_document
from .conformance import inspect_docx
from .layout import plan_document
from .model import InvalidSource, Source, fail, to_data


def office_executable():
    found = shutil.which("soffice")
    mac = Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")
    return found or (str(mac) if mac.is_file() else None)


def office_convert(executable, source, target_dir, fmt, user_dir):
    target_dir.mkdir(parents=True, exist_ok=True)
    result = run_tool([executable, "-env:UserInstallation=" + user_dir.resolve().as_uri(), "--headless", "--convert-to", fmt, "--outdir", str(target_dir), str(source)])
    extension = fmt.split(":")[0]
    output = target_dir / (source.stem + "." + extension)
    if not output.is_file():
        fail("office-conversion", result.stdout.decode(errors="replace") + result.stderr.decode(errors="replace") or "LibreOffice produced no file", Source(str(source), 1))
    return output


def build_document(source, profile, output, *, refresh=False, pdf=False):
    output = Path(output)
    if output.exists() and not output.is_dir():
        fail("output-exists", "Output path exists and is not a directory", Source(str(output), 1))
    parsed = parse_document(Path(source), Path(profile))
    plan = plan_document(parsed, Path(profile))
    with TemporaryDirectory(prefix="doc-formatter-") as temporary:
        work = Path(temporary)
        docx, version = emit(plan, work)
        report = inspect_docx(docx, plan)
        if report["findings"]:
            fail("conformance-failed", json.dumps(report["findings"], ensure_ascii=False), Source("document.docx", 1))
        report["tools"] = {"pandoc": version}
        report["field_refresh"] = "not-run"
        office = office_executable()
        if refresh and office:
            try:
                refreshed = office_convert(office, docx, work / "refresh", "docx:Office Open XML Text", work / "office-profile")
                refreshed_report = inspect_docx(refreshed, plan)
                if refreshed_report["findings"]:
                    report["field_refresh"] = "rejected"
                    report["refresh_findings"] = refreshed_report["findings"]
                else:
                    shutil.copyfile(refreshed, docx)
                    report["field_refresh"] = "passed"
            except InvalidSource as exc:
                report["field_refresh"] = "failed"
                report["refresh_findings"] = to_data(exc.diagnostics)
        if report["field_refresh"] != "passed":
            report["findings"].append({"severity": "warning", "code": "manual-field-refresh", "message": "Computed field values are included. Refresh fields in Word after editing; LibreOffice refresh was unavailable, not requested, or did not preserve the package checks."})
        if office and (refresh or pdf):
            report["tools"]["libreoffice"] = run_tool([office, "--version"]).stdout.decode().strip()
        generated_pdf = None
        if pdf:
            if not office:
                fail("missing-libreoffice", "Install LibreOffice to generate a PDF preview", Source("soffice", 1))
            generated_pdf = office_convert(office, docx, work / "pdf", "pdf", work / "pdf-profile")
        report["limitations"] = ["Sample-only conformance; no full-thesis certification.", "No Word desktop interaction has been performed by the build command.", "Cover and indexes are not part of this sample backend."]
        output.parent.mkdir(parents=True, exist_ok=True)
        # Stage all deliverables next to the target, then publish in one rename.
        with TemporaryDirectory(prefix=".doc-formatter-", dir=output.parent) as staging:
            bundle = Path(staging) / "bundle"
            bundle.mkdir()
            shutil.copyfile(docx, bundle / "document.docx")
            (bundle / "layout-plan.json").write_text(json.dumps(to_data(plan), ensure_ascii=False, indent=2) + "\n")
            (bundle / "conformance.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
            if generated_pdf:
                shutil.copyfile(generated_pdf, bundle / "document.pdf")
            if output.exists():
                if not output.is_dir():
                    fail("output-exists", "Output path exists and is not a directory", Source(str(output), 1))
                shutil.rmtree(output)
            bundle.rename(output)
    return report
