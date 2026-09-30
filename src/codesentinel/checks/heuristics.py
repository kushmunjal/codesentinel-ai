def check_heuristics(diff_text: str) -> list[str]:
    warnings = []
    lines = diff_text.split("\n")
    additions = sum(1 for line in lines if line.startswith("+") and not line.startswith("+++"))
    if additions > 500:
        warnings.append(f"Large PR detected ({additions} additions). Consider breaking it down.")
        
    has_tests = any("test" in line.lower() for line in lines if line.startswith("diff --git"))
    if additions > 50 and not has_tests:
        warnings.append("PR contains code additions but no tests seem to be included.")
        
    return warnings
