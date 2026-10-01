# ruff: noqa: E501
"""Generate every manuscript number, table, claim macro, figure, and bibliography entry.

All inputs come from the frozen SG-000023 paper evidence package and the SG-000024 verified
bibliography record. Nothing here performs inference or recomputes a scientific result; values are
copied from canonical artifacts and only formatted for presentation.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "registry" / "p08_sg000023_paper_evidence"
BIBLIOGRAPHY_PATH = ROOT / "registry" / "p09_sg000024_bibliography.json"
RELATED_WORK_PATH = ROOT / "registry" / "p08_sg000023_related_work_refresh.json"
DEFAULT_OUTPUT = ROOT / "paper" / "generated"

FROZEN_CLAIM_SET_SHA256 = "ef2e347d9ef4298deb68a422c063aa92e9968ae5d00fb0c511576448eb7a2b9b"
MANIFEST_NAME = "manifest.json"

SYSTEM_LABELS = {
    "paper": "DAL paper system",
    "clinical_control": "Clinical control",
    "laya": "Laya",
}
FHIR_SYSTEM_LABELS = {
    "gax-paper-candidate": "DAL paper system",
    "clinical-encoder": "Clinical control",
    "laya": "Laya",
}

LATEX_SPECIALS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def _load(name: str) -> Any:
    return json.loads((PACKAGE / name).read_text(encoding="utf-8"))


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tex_escape(text: str) -> str:
    return "".join(LATEX_SPECIALS.get(char, char) for char in text)


def fmt(value: float | int | None, decimals: int = 4) -> str:
    if value is None:
        return "--"
    if isinstance(value, bool):
        raise TypeError("boolean is not a manuscript number")
    if isinstance(value, int):
        return str(value)
    return f"{value:.{decimals}f}"


def verify_package() -> dict[str, Any]:
    """Fail closed unless the committed package matches its provenance index and frozen claims."""
    provenance = _load("provenance_index.json")
    for name, digest in provenance["artifact_sha256"].items():
        path = PACKAGE / name
        text = path.read_text(encoding="utf-8")
        if _sha256(text.encode("utf-8")) != digest:
            raise ValueError(f"paper evidence artifact differs from provenance index: {name}")
    freeze = _load("claim_freeze_manifest.json")
    if freeze["claim_freeze"]["claim_set_sha256"] != FROZEN_CLAIM_SET_SHA256:
        raise ValueError("claim set differs from the SG-000024 frozen binding")
    return provenance


# ---------------------------------------------------------------- numbers


def _numbers() -> dict[str, str]:
    main = _load("main_results.json")
    selective = _load("selective_results.json")
    fhir = _load("fhir_block_table.json")
    qualitative = _load("qualitative_examples.json")
    numbers: dict[str, str] = {}
    for row in main["rows"]:
        prefix = f"pubmedqa.{row['system_id']}"
        numbers[f"{prefix}.requested"] = fmt(row["requested"])
        numbers[f"{prefix}.completed"] = fmt(row["completed"])
        for metric, value in row["metrics"].items():
            numbers[f"{prefix}.{metric}"] = fmt(value)
    comparison = main["primary_comparison_display"]
    numbers["pubmedqa.diff.estimate"] = comparison["estimate"]
    numbers["pubmedqa.diff.cilow"] = comparison["ci_low"]
    numbers["pubmedqa.diff.cihigh"] = comparison["ci_high"]
    numbers["pubmedqa.bootstrap.replicates"] = fmt(
        main["primary_comparison"]["paired_bootstrap"]["replicates"]
    )
    numbers["pubmedqa.bootstrap.seed"] = fmt(main["primary_comparison"]["paired_bootstrap"]["seed"])
    identity = main["paper_control_action_identity"]
    numbers["pubmedqa.identity.rows"] = fmt(identity["rows"])
    numbers["pubmedqa.identity.probabilities"] = fmt(identity["identical_action_probability_rows"])
    for row in selective["rows"]:
        prefix = f"native.{row['system_id']}"
        numbers[f"{prefix}.requested"] = fmt(row["requested"])
        numbers[f"{prefix}.completed"] = fmt(row["completed"])
        numbers[f"{prefix}.failed"] = fmt(row["failed"])
        for metric, value in row["metrics"].items():
            numbers[f"{prefix}.{metric.replace('_', '')}"] = fmt(value)
        for target, policy in (row["actual_policy"] or {}).items():
            tag = target.replace(".", "")
            for field in (
                "threshold",
                "actual_coverage",
                "unsafe_commit_rate",
                "over_abstain_rate",
            ):
                numbers[f"{prefix}.target{tag}.{field.replace('_', '')}"] = fmt(policy[field])
    native_comparison = selective["primary_comparison_display"]
    numbers["native.diff.estimate"] = native_comparison["estimate"]
    numbers["native.diff.cilow"] = native_comparison["ci_low"]
    numbers["native.diff.cihigh"] = native_comparison["ci_high"]
    native_identity = selective["paper_control_action_identity"]
    numbers["native.identity.rows"] = fmt(native_identity["rows"])
    numbers["native.identity.correctness"] = fmt(
        native_identity["identical_action_correctness_rows"]
    )
    numbers["native.identity.scores"] = fmt(native_identity["identical_selection_score_rows"])
    requested = sorted({row["requested"] for row in fhir["rows"]})
    failures = sorted({row["interface_failures"] for row in fhir["rows"]})
    if len(requested) != 1 or len(failures) != 1:
        raise ValueError("FHIR block rows disagree on denominator or failures")
    numbers["fhir.requested"] = fmt(requested[0])
    numbers["fhir.interfacefailures"] = fmt(failures[0])
    numbers["fhir.goldrows"] = fmt(fhir["rows"][0]["gold_rows_loaded"])
    numbers["fhir.systems"] = fmt(len(fhir["rows"]))
    for stratum in qualitative["pubmedqa_strata"] + qualitative["native_strata"]:
        numbers[f"errors.{stratum['id']}"] = fmt(stratum["member_count"])
    numbers["errors.perstratum"] = fmt(qualitative["selection_count_per_stratum"])
    return dict(sorted(numbers.items()))


def _numbers_tex(numbers: dict[str, str]) -> str:
    lines = [
        "% Generated by tools/build_sg000024_manuscript_inputs.py; do not edit.",
        "% Every value is copied from registry/p08_sg000023_paper_evidence and formatted for display.",
        "\\makeatletter",
        "\\newcommand{\\dalnum}[1]{\\ifcsname dalnum@#1\\endcsname\\csname dalnum@#1\\endcsname\\else\\PackageError{dal}{Undefined DAL number #1}{}\\fi}",
    ]
    for key, value in numbers.items():
        lines.append(f"\\expandafter\\def\\csname dalnum@{key}\\endcsname{{{value}}}")
    lines.append("\\makeatother")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- claims


def _claims_tex() -> str:
    ledger = _load("claim_ledger.json")
    lines = [
        "% Generated by tools/build_sg000024_manuscript_inputs.py; do not edit.",
        "% \\dalclaim{ID} expands to the frozen permitted wording of an affirmative claim.",
        "% \\dallimitation{ID} expands to the frozen wording of a limitation statement.",
        "\\makeatletter",
        "\\newcommand{\\dalclaim}[1]{\\ifcsname dalclaim@#1\\endcsname\\csname dalclaim@#1\\endcsname\\else\\PackageError{dal}{#1 is not an exportable frozen claim}{}\\fi}",
        "\\newcommand{\\dallimitation}[1]{\\ifcsname dallimitation@#1\\endcsname\\csname dallimitation@#1\\endcsname\\else\\PackageError{dal}{#1 is not a frozen limitation statement}{}\\fi}",
    ]
    for claim in ledger["claims"]:
        family = "dalclaim" if claim["public_use"] == "affirmative-claim" else "dallimitation"
        lines.append(
            f"\\expandafter\\def\\csname {family}@{claim['claim_id']}\\endcsname{{{tex_escape(claim['text'])}}}"
        )
    lines.append("\\makeatother")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- tables


def _table(
    caption: str, label: str, spec: str, header: list[str], rows: list[list[str]], note: str
) -> str:
    lines = [
        "% Generated by tools/build_sg000024_manuscript_inputs.py; do not edit.",
        "\\begin{table}[t]",
        "\\centering",
        "\\small",
        f"\\caption{{{caption}}}",
        f"\\label{{{label}}}",
        f"\\begin{{tabular}}{{{spec}}}",
        "\\toprule",
        " & ".join(header) + " \\\\",
        "\\midrule",
    ]
    lines.extend(" & ".join(row) + " \\\\" for row in rows)
    lines.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            f"\\par\\smallskip\\parbox{{\\linewidth}}{{\\footnotesize {note}}}",
            "\\end{table}",
        ]
    )
    return "\n".join(lines) + "\n"


def _table_main() -> str:
    main = _load("main_results.json")
    rows = []
    for row in main["rows"]:
        metrics = row["metrics"]
        rows.append(
            [
                SYSTEM_LABELS[row["system_id"]],
                f"{row['completed']}/{row['requested']}",
                fmt(metrics["accuracy"]),
                fmt(metrics["macro_f1"]),
                fmt(metrics["nll"]),
                fmt(metrics["multiclass_brier"]),
                fmt(metrics["ece_15_equal_width"]),
            ]
        )
    comparison = main["primary_comparison_display"]
    note = tex_escape(
        f"Frozen PubMedQA PQA-L final rows. Paper-minus-control action-accuracy estimate {comparison['estimate']} "
        f"(95% paired-bootstrap interval [{comparison['ci_low']}, {comparison['ci_high']}]). Laya macro-F1 is not reported "
        "in canonical metrics, and Laya ECE is excluded because its affected confidence is uncalibrated. Values are rounded "
        "for display; unrounded values are in main_results.json."
    )
    return _table(
        "PubMedQA action selection on the frozen final rows.",
        "tab:main",
        "lrrrrrr",
        ["System", "Completed", "Accuracy", "Macro-F1", "NLL", "Brier", "ECE (15 bins)"],
        rows,
        note,
    )


def _table_selective() -> str:
    selective = _load("selective_results.json")
    rows = []
    for row in selective["rows"]:
        label = SYSTEM_LABELS[row["system_id"]]
        if row["status"] == "blocked":
            rows.append([label, "\\multicolumn{6}{l}{blocked: " + tex_escape(row["reason"]) + "}"])
            continue
        metrics = row["metrics"]
        rows.append(
            [
                label,
                fmt(metrics["risk_at_50"]),
                fmt(metrics["risk_at_80"]),
                fmt(metrics["risk_at_90"]),
                fmt(metrics["aurc"]),
                fmt(row["actual_policy"]["0.8"]["actual_coverage"]),
                fmt(row["actual_policy"]["0.8"]["unsafe_commit_rate"]),
            ]
        )
    comparison = selective["primary_comparison_display"]
    note = tex_escape(
        f"Native-abstention final rows; lower risk is better. Paper-minus-control risk@80 estimate {comparison['estimate']} "
        f"(95% paired-bootstrap interval [{comparison['ci_low']}, {comparison['ci_high']}]), reported descriptively. The last two "
        "columns show the frozen target-coverage-0.8 policy; the paper system's 0.8 and 0.9 policies both reached coverage 1.0 "
        "with unsafe-commit rate 1.0."
    )
    return _table(
        "Native abstention: selective risk and frozen target-policy outcomes.",
        "tab:selective",
        "lrrrrrr",
        ["System", "Risk@50", "Risk@80", "Risk@90", "AURC", "Cov.@0.8", "Unsafe@0.8"],
        rows,
        note,
    )


def _table_policy() -> str:
    selective = _load("selective_results.json")
    rows = []
    for row in selective["rows"]:
        if row["status"] == "blocked":
            continue
        for target, policy in sorted(row["actual_policy"].items()):
            rows.append(
                [
                    SYSTEM_LABELS[row["system_id"]],
                    target,
                    fmt(policy["threshold"], 6),
                    fmt(policy["actual_coverage"]),
                    fmt(policy["unsafe_commit_rate"]),
                    fmt(policy["over_abstain_rate"]),
                ]
            )
    note = tex_escape(
        "Thresholds were frozen before final-test access and were not refit. Thresholds are shown to 6 decimals."
    )
    return _table(
        "Frozen target-coverage policies on the native-abstention final rows.",
        "tab:policy",
        "lrrrrr",
        ["System", "Target", "Threshold", "Coverage", "Unsafe-commit", "Over-abstain"],
        rows,
        note,
    )


def _table_fhir() -> str:
    fhir = _load("fhir_block_table.json")
    rows = [
        [
            FHIR_SYSTEM_LABELS[row["system_id"]],
            fmt(row["requested"]),
            fmt(row["completed"]),
            fmt(row["interface_failures"]),
            fmt(row["gold_rows_loaded"]),
            tex_escape(row["status"]),
        ]
        for row in fhir["rows"]
    ]
    note = tex_escape(
        "Reason: "
        + fhir["rows"][0]["reason"]
        + ". Detected before final-test access; no replacement adapter was permitted."
    )
    return _table(
        "FHIR-AgentBench final action selection was blocked before execution.",
        "tab:fhir",
        "lrrrrl",
        ["System", "Requested", "Completed", "Interface failures", "Gold rows", "Status"],
        rows,
        note,
    )


def _table_boundaries() -> str:
    boundaries = _load("evidence_boundaries.json")
    rows = [
        [
            tex_escape(row["id"]),
            tex_escape(row["status"]),
            tex_escape(row["no_packet_reason"] or "packet records the blocked result"),
        ]
        for row in boundaries["rows"]
    ]
    return _table(
        "Analyses that the frozen evidence cannot support.",
        "tab:boundaries",
        "llp{0.55\\linewidth}",
        ["Analysis", "Status", "Reason"],
        rows,
        tex_escape("From the SG-000023 evidence-availability matrix."),
    )


def _table_ecal() -> str:
    ecal = _load("ecal_selection_table.json")
    p04 = {row["component"]: row["paper_decision"] for row in ecal["p04_development_status"]}
    rows = [
        [
            tex_escape(row["component"]),
            tex_escape(row["decision"]),
            "yes" if row["requires_retraining_or_checkpoint_mutation"] else "no",
            tex_escape(p04.get(row["component"], "no same-name P04 component")),
        ]
        for row in ecal["selection_rows"]
    ]
    return _table(
        "Frozen ECAL selection: compatibility with the frozen checkpoint, not measured benefit.",
        "tab:ecal",
        "llll",
        ["Component", "Decision", "Needs retraining", "P04 paper decision"],
        rows,
        tex_escape(ecal["boundary"]),
    )


def _table_claims() -> str:
    ledger = _load("claim_ledger.json")
    rows = [
        [
            tex_escape(claim["claim_id"]),
            tex_escape(claim["status"]),
            "affirmative" if claim["public_use"] == "affirmative-claim" else "limitation",
            tex_escape(claim["evidence_packet_id"] or "none"),
        ]
        for claim in ledger["claims"]
    ]
    freeze = _load("claim_freeze_manifest.json")
    return _table(
        "Frozen claim ledger.",
        "tab:claims",
        "llll",
        ["Claim", "Status", "Public use", "Evidence packet"],
        rows,
        tex_escape(
            "Claim-set SHA-256 "
            + freeze["claim_freeze"]["claim_set_sha256"]
            + ". Claim text appears verbatim in the manuscript through generated macros."
        ),
    )


def _table_errors() -> str:
    qualitative = _load("qualitative_examples.json")
    rows = [
        [tex_escape(stratum["id"]), fmt(stratum["member_count"]), fmt(len(stratum["selected"]))]
        for stratum in qualitative["pubmedqa_strata"] + qualitative["native_strata"]
    ]
    return _table(
        "Content-blind failure strata on the frozen final rows.",
        "tab:errors",
        "lrr",
        ["Stratum", "Members", "Selected examples"],
        rows,
        tex_escape(
            "Native strata use the frozen target-coverage-0.8 thresholds. Examples were selected by a rule frozen before inspection: "
            + qualitative["ranking"]
            + "."
        ),
    )


# ---------------------------------------------------------------- figures


def _coords(points: list[tuple[float, float]]) -> str:
    return " ".join(f"({x:.6f},{y:.6f})" for x, y in points)


PLOT_STYLE = {"paper": "blue, thick", "clinical_control": "orange, thick, dashed"}


def _figure_reliability() -> str:
    source = _load("reliability_source_data.json")
    lines = [
        "% Generated by tools/build_sg000024_manuscript_inputs.py from reliability_source_data.json; do not edit.",
        "\\begin{tikzpicture}",
        "\\begin{axis}[width=0.48\\linewidth, xmin=0, xmax=1, ymin=0, ymax=1, xlabel={Mean confidence}, ylabel={Accuracy}, legend pos=north west, legend style={font=\\scriptsize}]",
        "\\addplot[gray, dotted, domain=0:1] {x};",
        "\\addlegendentry{perfect calibration}",
    ]
    for system in source["systems"]:
        points = [
            (row["mean_confidence"], row["accuracy"]) for row in system["bins"] if row["count"] > 0
        ]
        lines.append(
            f"\\addplot[{PLOT_STYLE[system['system_id']]}, mark=*] coordinates {{{_coords(points)}}};"
        )
        lines.append(f"\\addlegendentry{{{SYSTEM_LABELS[system['system_id']]}}}")
    lines.extend(["\\end{axis}", "\\end{tikzpicture}"])
    return "\n".join(lines) + "\n"


def _figure_risk_coverage() -> str:
    source = _load("risk_coverage_source_data.json")
    lines = [
        "% Generated by tools/build_sg000024_manuscript_inputs.py from risk_coverage_source_data.json; do not edit.",
        "\\begin{tikzpicture}",
        "\\begin{axis}[width=0.48\\linewidth, xmin=0, xmax=1, ymin=0, ymax=1, xlabel={Coverage}, ylabel={Selective risk}, legend pos=north west, legend style={font=\\scriptsize}]",
    ]
    for system in source["systems"]:
        points = [(point["coverage"], point["risk"]) for point in system["points"]]
        lines.append(
            f"\\addplot[{PLOT_STYLE[system['system_id']]}] coordinates {{{_coords(points)}}};"
        )
        lines.append(f"\\addlegendentry{{{SYSTEM_LABELS[system['system_id']]}}}")
    for target in (0.5, 0.8, 0.9):
        lines.append(f"\\draw[gray, dotted] (axis cs:{target},0) -- (axis cs:{target},1);")
    lines.extend(["\\end{axis}", "\\end{tikzpicture}"])
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- bibliography


def _bib_escape(text: str) -> str:
    return (
        html.unescape(text)
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("#", r"\#")
        .replace("_", r"\_")
    )


def _bibliography() -> str:
    record = json.loads(BIBLIOGRAPHY_PATH.read_text(encoding="utf-8"))
    related = json.loads(RELATED_WORK_PATH.read_text(encoding="utf-8"))
    peer_venues = {
        entry["identifiers"]["arxiv"]: entry["venue"]
        for entry in related["included"]
        if "arxiv" in entry["identifiers"] and not entry["venue"].startswith("arXiv")
    }
    blocks = [
        "% Generated by tools/build_sg000024_manuscript_inputs.py from registry/p09_sg000024_bibliography.json; do not edit."
    ]
    for entry in sorted(record["entries"], key=lambda row: row["key"]):
        fields: dict[str, str] = {"title": "{" + _bib_escape(entry["title"]) + "}"}
        if entry["authors"]:
            fields["author"] = (
                "{" + " and ".join(_bib_escape(name) for name in entry["authors"]) + "}"
            )
        else:
            fields["author"] = "{{TypeSafe AI}}"
        fields["year"] = "{" + str(entry["year"]) + "}"
        fields["url"] = "{" + entry["url"] + "}"
        if entry["kind"] == "doi":
            entry_type = "article"
            fields["journal"] = "{" + _bib_escape(entry["venue"]) + "}"
            fields["doi"] = "{" + entry["doi"] + "}"
        elif entry["kind"] == "arxiv":
            entry_type = "misc"
            venue = peer_venues.get(entry["arxiv"])
            note = f"arXiv:{entry['arxiv']}" + (
                f"; {venue}" if venue else "; preprint, not peer reviewed"
            )
            fields["howpublished"] = "{" + _bib_escape(note) + "}"
            fields["eprint"] = "{" + entry["arxiv"] + "}"
            fields["archiveprefix"] = "{arXiv}"
        else:
            entry_type = "misc"
            fields["howpublished"] = "{" + _bib_escape(entry["venue"]) + "}"
        body = ",\n".join(f"  {name} = {value}" for name, value in fields.items())
        blocks.append(f"@{entry_type}{{{entry['key']},\n{body}\n}}")
    return "\n\n".join(blocks) + "\n"


# ---------------------------------------------------------------- build


GENERATORS: dict[str, Callable[[], str]] = {
    "dal_claims.tex": _claims_tex,
    "fig_reliability.tex": _figure_reliability,
    "fig_risk_coverage.tex": _figure_risk_coverage,
    "references.bib": _bibliography,
    "tab_boundaries.tex": _table_boundaries,
    "tab_claims.tex": _table_claims,
    "tab_ecal.tex": _table_ecal,
    "tab_errors.tex": _table_errors,
    "tab_fhir.tex": _table_fhir,
    "tab_main.tex": _table_main,
    "tab_policy.tex": _table_policy,
    "tab_selective.tex": _table_selective,
}


def build_outputs() -> dict[str, str]:
    provenance = verify_package()
    outputs = {"dal_numbers.tex": _numbers_tex(_numbers())}
    outputs.update({name: generator() for name, generator in GENERATORS.items()})
    manifest = {
        "schema_version": "0.1",
        "grain_id": "SG-000024",
        "generator": "tools/build_sg000024_manuscript_inputs.py",
        "paper_evidence_root": "registry/p08_sg000023_paper_evidence",
        "paper_evidence_artifact_sha256": provenance["artifact_sha256"],
        "frozen_claim_set_sha256": FROZEN_CLAIM_SET_SHA256,
        "bibliography_record_sha256": _sha256(BIBLIOGRAPHY_PATH.read_bytes()),
        "outputs_sha256": {
            name: _sha256(text.encode("utf-8")) for name, text in sorted(outputs.items())
        },
    }
    outputs[MANIFEST_NAME] = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    return dict(sorted(outputs.items()))


def check_outputs(output_dir: Path, outputs: dict[str, str]) -> list[str]:
    errors = []
    actual = (
        {path.name for path in output_dir.iterdir() if path.is_file()}
        if output_dir.is_dir()
        else set()
    )
    if actual != set(outputs):
        errors.append(
            f"generated file set mismatch: actual={sorted(actual)} expected={sorted(outputs)}"
        )
    for name, text in outputs.items():
        path = output_dir / name
        if path.is_file() and path.read_text(encoding="utf-8") != text:
            errors.append(f"generated file differs from deterministic rebuild: {name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build SG-000024 manuscript inputs from frozen evidence"
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check", action="store_true", help="fail unless committed outputs match a rebuild"
    )
    args = parser.parse_args()
    outputs = build_outputs()
    if args.check:
        errors = check_outputs(args.output_dir, outputs)
        for error in errors:
            print(error)
        if errors:
            return 1
        print(f"SG-000024 manuscript inputs check passed: {len(outputs)} files")
        return 0
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, text in outputs.items():
        (args.output_dir / name).write_text(text, encoding="utf-8", newline="\n")
    print(f"SG-000024 manuscript inputs built: {len(outputs)} files -> {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
