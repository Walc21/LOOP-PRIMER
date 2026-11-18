"""Independent verification for one explicitly bounded synthetic article."""
from pathlib import Path

from article_loop.blackboard import Blackboard
from article_loop.gates import (
    _manifest, _math_requests, _proposals, _synthesis, record_math_verification,
)
from article_loop.synthesis import IntegrityError, _contained, _regular


BASE_SOURCE = (
    "\\documentclass{article}\n\\begin{document}\n"
    "If $x=1$, then $x+x=2$. Proof: substitute.\\label{lemma}\n"
    "\\end{document}\n"
)
REVISED_SOURCE = BASE_SOURCE.replace(
    "Proof: substitute.", "Proof: substituting $x=1$ gives $x+x=1+1=2$."
)
APPROVED_REVISIONS = (REVISED_SOURCE, REVISED_SOURCE.removesuffix("\n"))
CLAIM = "If x=1, then x+x=2"


def verify_synthetic_candidate(candidate: Path) -> list[dict]:
    """Verify exactly the fixed synthetic proposition and its allowed revisions."""
    candidate = Path(candidate)
    if candidate.is_symlink():
        raise IntegrityError("synthetic candidate is symlinked")
    candidate = candidate.resolve()
    root = candidate.parents[2]
    manifest = _manifest(root, candidate)
    synthesis = _synthesis(root, manifest)
    proposals = _proposals(root, manifest, synthesis)
    requests = _math_requests(proposals)
    baseline = _contained(root, "versions/champion/v0000/latex-source/paper.tex", True)
    revised = _contained(root, f"versions/challengers/{manifest['candidate_id']}/latex-source/paper.tex", True)
    _regular(baseline)
    _regular(revised)
    if baseline.read_text(encoding="utf-8") != BASE_SOURCE:
        raise IntegrityError("synthetic baseline differs from fixed article")
    if revised.read_bytes() not in tuple(source.encode("utf-8") for source in (BASE_SOURCE, *APPROVED_REVISIONS)):
        raise IntegrityError("synthetic candidate changes the assertion or proof")
    tex_files = {path.relative_to(candidate).as_posix() for path in candidate.rglob("*.tex")}
    if tex_files != {"latex-source/paper.tex", "source/reconstructed.tex"}:
        raise IntegrityError("synthetic candidate contains unexpected TeX sources")
    reconstructed = _contained(root, f"versions/challengers/{manifest['candidate_id']}/source/reconstructed.tex", True)
    original_reconstruction = _contained(root, "versions/champion/v0000/source/reconstructed.tex", True)
    _regular(reconstructed)
    _regular(original_reconstruction)
    if reconstructed.read_bytes() != original_reconstruction.read_bytes():
        raise IntegrityError("synthetic reconstructed source was changed")
    claims = {item.get("record_id") or item.get("claim_id"): item
              for item in Blackboard(root).read(manifest["run_id"], "claims")}
    if len(requests) != 1:
        raise IntegrityError("synthetic verification requires exactly one W22 claim")
    (proposal_id, claim_id), = requests
    claim = claims.get(claim_id)
    if not claim or claim.get("text") != CLAIM or claim.get("type") != "theorem":
        raise IntegrityError("synthetic claim differs from fixed theorem")
    if 1 + 1 != 2:
        raise IntegrityError("synthetic arithmetic verification failed")
    return [record_math_verification(
        candidate, claim_id=claim_id, proposal_id=proposal_id,
        verifier_id="synthetic-arithmetic", verifier_version="1.0.0",
        method="independent-recalculation",
        summary="For the fixed synthetic theorem, substitution gives 1 + 1 = 2.",
    )]
