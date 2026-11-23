import sys
try:
    import pypdf
except Exception as e:
    print("nopypdf", e); sys.exit()
r = pypdf.PdfReader(r"C:\Users\tatsu\.claude\projects\C--Users-tatsu-claudecode\61f58174-d95a-4d7b-858b-879f8f66a149\tool-results\webfetch-1794794952472-s3ru0g.pdf")
out = []
for i, p in enumerate(r.pages):
    out.append("=== p%d ===\n" % (i + 1) + (p.extract_text() or ""))
open(r"C:\Users\tatsu\claudecode\tsunakare-clubs\docs\serp-notes\_tmp_rule_m.txt", "w", encoding="utf-8").write("\n".join(out))
print(len(r.pages))
