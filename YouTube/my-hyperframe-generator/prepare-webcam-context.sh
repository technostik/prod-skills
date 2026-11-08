#!/usr/bin/env bash
set -euo pipefail

# Usage : ./prepare-webcam-context.sh /chemin/vers/destination [--project /chemin/vers/projet]
#                                      [--mode webcam|incrustation]
#
# --mode (défaut : webcam) : sous-skill ajouté à storyboard/ (modes/webcam.md ou modes/incrustation.md).
#
# --project (facultatif) : ajoute à storyboard/ les données du projet utiles à l'annotation des
# séquences Cast : assets/cast-segments.json (s'il existe) et transcript.json.

PROJECT=""
MODE="webcam"
POSITIONAL=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --project)
            [[ $# -ge 2 ]] || { echo "ERREUR : --project demande un répertoire" >&2; exit 1; }
            PROJECT="$(realpath -m "$2")"
            shift 2
            ;;
        --mode)
            [[ $# -ge 2 ]] || { echo "ERREUR : --mode demande webcam ou incrustation" >&2; exit 1; }
            MODE="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage : $0 <répertoire-de-destination> [--project <répertoire-du-projet>] [--mode webcam|incrustation]"
            exit 0
            ;;
        *)
            POSITIONAL+=("$1")
            shift
            ;;
    esac
done

if [[ ${#POSITIONAL[@]} -ne 1 ]]; then
    echo "Usage : $0 <répertoire-de-destination> [--project <répertoire-du-projet>] [--mode webcam|incrustation]" >&2
    exit 1
fi
if [[ "$MODE" != "webcam" && "$MODE" != "incrustation" ]]; then
    echo "ERREUR : --mode doit valoir webcam ou incrustation (reçu : $MODE)" >&2
    exit 1
fi

DEST="$(realpath -m "${POSITIONAL[0]}")"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

COMMUN="$DEST/commun"
STORYBOARD="$DEST/storyboard"
COMPOSITION="$DEST/composition"

mkdir -p "$COMMUN" "$STORYBOARD" "$COMPOSITION"

# Copie avec vérification de l'existence du fichier.
copy_file() {
    local source="$1"
    local target="$2"

    if [[ ! -f "$source" ]]; then
        echo "ERREUR : fichier introuvable : $source" >&2
        exit 1
    fi

    cp "$source" "$target/"
}

# --------------------------------------------------
# COMMUN
# --------------------------------------------------

copy_file "$ROOT/SKILL.md" "$COMMUN"
copy_file "$ROOT/references/visual-language-joriel.md" "$COMMUN"

# --------------------------------------------------
# STORYBOARD — mode webcam
# --------------------------------------------------

copy_file "$ROOT/references/storyboard-format.md" "$STORYBOARD"
copy_file "$ROOT/references/scenario-to-storyboard-prompt.md" "$STORYBOARD"
# Demandés par le prompt de scénarisation (schémas des fichiers de données ; caméra, dont Cast)
copy_file "$ROOT/references/data-schemas.md" "$STORYBOARD"
copy_file "$ROOT/references/webcam.md" "$STORYBOARD"
# Sous-skill du mode, sous un nom distinct (références/webcam.md porte déjà `webcam.md` dans ce dossier)
if [[ -f "$ROOT/modes/$MODE.md" ]]; then
    cp "$ROOT/modes/$MODE.md" "$STORYBOARD/mode-$MODE.md"
else
    echo "AVERTISSEMENT : $ROOT/modes/$MODE.md absent" >&2
fi
copy_file "$ROOT/references/posthoc-video-conventions.md" "$STORYBOARD"
copy_file "$ROOT/references/scenario-studio-conventions.md" "$STORYBOARD"

# Données du projet pour les séquences Cast (facultatif)
if [[ -n "$PROJECT" ]]; then
    if [[ -f "$PROJECT/assets/cast-segments.json" ]]; then
        cp "$PROJECT/assets/cast-segments.json" "$STORYBOARD/"
    else
        echo "AVERTISSEMENT : $PROJECT/assets/cast-segments.json absent (pas de Cast, ou lancer scripts/detect-cast.py)" >&2
    fi
    if [[ -f "$PROJECT/transcript.json" ]]; then
        cp "$PROJECT/transcript.json" "$STORYBOARD/"
    elif [[ -f "$PROJECT/assets/transcript.json" ]]; then
        cp "$PROJECT/assets/transcript.json" "$STORYBOARD/"
    else
        echo "AVERTISSEMENT : transcript.json introuvable dans $PROJECT" >&2
    fi
fi

# --------------------------------------------------
# COMPOSITION
# --------------------------------------------------

copy_file "$ROOT/references/primitives-joriel.md" "$COMPOSITION"
copy_file "$ROOT/examples/storyboard.example.md" "$COMPOSITION"

# Exemples HTML de composition
mkdir -p "$COMPOSITION/compositions"

shopt -s nullglob
COMPOSITIONS=("$ROOT"/examples/demo/compositions/i*.html)
shopt -u nullglob

if [[ ${#COMPOSITIONS[@]} -eq 0 ]]; then
    echo "ERREUR : aucun exemple i*.html trouvé." >&2
    exit 1
fi

#for file in "${COMPOSITIONS[@]}"; do
#    cp "$file" "$COMPOSITION/compositions/"
#done


# Démonstration et feuille de style
copy_file "$ROOT/examples/demo/index.html" "$COMPOSITION"
mkdir -p "$COMPOSITION/assets"
copy_file "$ROOT/examples/demo/assets/style-joriel.css" "$COMPOSITION/assets"

echo
echo "Contexte webcam préparé dans : $DEST"
echo
find "$DEST" -type f | sort

# Fusion des compositions
# ------------------------------------------------------------
# Exemples HTML de composition : fusion des sections
# ------------------------------------------------------------

mkdir -p "$COMPOSITION"

shopt -s nullglob
COMPOSITIONS=("$ROOT"/examples/demo/compositions/i*.html)
shopt -u nullglob

if [[ ${#COMPOSITIONS[@]} -eq 0 ]]; then
    echo "ERREUR : aucun exemple i*.html trouvé." >&2
    exit 1
fi

OUTPUT="$COMPOSITION/composition-examples.html"

python3 - "$OUTPUT" "${COMPOSITIONS[@]}" <<'PY'
import re
import sys
from pathlib import Path

output = Path(sys.argv[1])
files = [Path(p) for p in sys.argv[2:]]

# Repère le contenu d'un template HTML.
TEMPLATE_RE = re.compile(
    r'(<template\b[^>]*>)(.*?)(</template\s*>)',
    re.IGNORECASE | re.DOTALL
)

# Repère les balises section ouvrantes et fermantes.
SECTION_TAG_RE = re.compile(
    r'<\s*(/?)\s*section\b[^>]*>',
    re.IGNORECASE
)

def extract_template(content, filename):
    match = TEMPLATE_RE.search(content)
    if not match:
        raise ValueError(f"{filename} : balise <template> introuvable")
    return match.group(1), match.group(2), match.group(3), match

def extract_sections(template_content, filename):
    sections = []
    depth = 0
    start = None

    for match in SECTION_TAG_RE.finditer(template_content):
        closing = bool(match.group(1))

        if not closing:
            if depth == 0:
                start = match.start()
            depth += 1
        else:
            if depth == 0:
                continue
            depth -= 1
            if depth == 0 and start is not None:
                sections.append(template_content[start:match.end()])
                start = None

    if depth != 0:
        raise ValueError(f"{filename} : section HTML non refermée")

    return sections

# Le premier fichier sert de squelette : head, root, styles,
# structure extérieure et scripts restent inchangés.
base = files[0]
base_content = base.read_text(encoding="utf-8")
open_tag, base_template, close_tag, base_match = extract_template(
    base_content, base.name
)

base_sections = extract_sections(base_template, base.name)

if not base_sections:
    raise SystemExit(f"ERREUR : aucune section trouvée dans {base.name}")

# On conserve tout ce qui précède la première section et tout
# ce qui suit la dernière section du fichier de référence.
prefix = base_template[:base_template.find(base_sections[0])]
last_section_end = base_template.rfind(base_sections[-1]) + len(base_sections[-1])
suffix = base_template[last_section_end:]

# On récupère les sections de tous les exemples.
merged_sections = []

for file in files:
    content = file.read_text(encoding="utf-8")
    _, template, _, _ = extract_template(content, file.name)
    sections = extract_sections(template, file.name)

    if not sections:
        print(f"ATTENTION : aucune section dans {file.name}", file=sys.stderr)
        continue

    merged_sections.append(f"\n<!-- EXEMPLES DE {file.name} -->\n")
    merged_sections.extend(sections)

    print(f"  {file.name} : {len(sections)} section(s)")

if not merged_sections:
    raise SystemExit("ERREUR : aucune section à fusionner")

# On remplace uniquement le contenu du template du fichier de base.
merged_template = (
    open_tag
    + prefix
    + "\n".join(merged_sections)
    + "\n"
    + suffix
    + close_tag
)

result = (
    base_content[:base_match.start()]
    + merged_template
    + base_content[base_match.end():]
)

output.write_text(result, encoding="utf-8")

print(f"\nFichier généré : {output}")
print(f"Total : {len(merged_sections)} blocs extraits")
PY

if [[ ! -s "$OUTPUT" ]]; then
    echo "ERREUR : le fichier de composition n'a pas été généré." >&2
    exit 1
fi

echo "Exemples de composition regroupés dans : $OUTPUT"
