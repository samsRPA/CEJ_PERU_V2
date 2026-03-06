import re

# Archivos
INPUT_FILE = "sinradicados.csv"      # tu archivo de logs
OUTPUT_FILE = "radicados_no_encontrados.txt"

# Regex para capturar el radicado
# Ejemplo:
# ❌ No se encontraron expedientes tras 4 intentos para el radicado 00112-2011-20-1829-JP-CI-01
pattern = re.compile(
    r"No se encontraron expedientes tras \d+ intentos para el radicado\s+([0-9A-Z\-]+)"
)

radicados = set()  # usamos set para evitar duplicados

with open(INPUT_FILE, "r", encoding="utf-8", errors="ignore") as file:
    for line in file:
        match = pattern.search(line)
        if match:
            radicado = match.group(1)
            radicados.add(radicado)

# Guardar en TXT
with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
    for r in sorted(radicados):
        out.write(r + "\n")

print(f"✅ Se extrajeron {len(radicados)} radicados.")
print(f"📄 Archivo generado: {OUTPUT_FILE}")
