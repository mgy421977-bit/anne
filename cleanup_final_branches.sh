#!/bin/bash

# Son gereksiz brançları sil
BRANCHES=(
  "anne-mitos-subconscious-20260906-v3"
  "anne-runtime-simulation-20260906"
  "anne-web-research-20260906"
)

echo "=========================================="
echo "ANNE Repository - Final Cleanup"
echo "=========================================="
echo "Silinecek branch sayısı: ${#BRANCHES[@]}"
echo ""

DELETED=0
FAILED=0

for BRANCH in "${BRANCHES[@]}"; do
  printf "%-50s " "Siliniyor: $BRANCH"
  if git push origin --delete "$BRANCH" 2>&1 | grep -q "deleted"; then
    echo "✓ OK"
    ((DELETED++))
  else
    echo "✗ HATA"
    ((FAILED++))
  fi
done

echo ""
echo "=========================================="
echo "ÖZET"
echo "=========================================="
echo "✓ Başarıyla silindi: $DELETED"
echo "✗ Başarısız: $FAILED"
echo "=========================================="
