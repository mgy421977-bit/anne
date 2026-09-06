#!/bin/bash

# Silinecek brançların tam listesi
BRANCHES=(
  "anne-computation-merge-20260905-final2"
  "anne-computation-merge-work"
  "anne-computation-merge-work2"
  "anne-language-online-learning-20260905-mathmerge"
  "anne-language-online-learning-20260905-mathmerge2"
  "anne-language-online-learning-20260905-mathmerge3"
  "anne-language-online-learning-20260905-merge"
  "anne-language-online-learning-20260905-symbolic"
  "anne-language-online-learning-20260905-symbolic2"
  "anne-dxf-engine-20260906"
  "anne-excel-calculation-engine-20260906"
  "anne-experience-learning-20260906"
  "anne-language-core-20260906"
  "anne-unified-computation-20260905b"
  "anne-unified-computation-20260905c"
  "anne-unified-computation-clean-20260905"
  "anne-unified-20260905"
  "anne-unified-20260905x"
  "anne-merge-final"
  "anne-unified-final"
  "anne-unified-merge-final"
  "anne-runtime-stability-20260903"
  "anne-ci-fix-20260903"
  "anne-architecture-cleanup-20260904"
  "anne-github-write-tools-20260904"
  "anne-tinker-ollama-files-20260904"
)

echo "=========================================="
echo "ANNE Repository Branch Cleanup"
echo "=========================================="
echo "Silinecek branch sayısı: ${#BRANCHES[@]}"
echo ""

DELETED=0
FAILED=0
FAILED_BRANCHES=()

for BRANCH in "${BRANCHES[@]}"; do
  printf "%-60s " "Siliniyor: $BRANCH"
  if git push origin --delete "$BRANCH" 2>&1 | grep -q "deleted"; then
    echo "✓ OK"
    ((DELETED++))
  else
    echo "✗ HATA"
    ((FAILED++))
    FAILED_BRANCHES+=("$BRANCH")
  fi
done

echo ""
echo "=========================================="
echo "ÖZET"
echo "=========================================="
echo "✓ Başarıyla silindi: $DELETED"
echo "✗ Başarısız: $FAILED"

if [ $FAILED -gt 0 ]; then
  echo ""
  echo "Başarısız brançlar:"
  for BRANCH in "${FAILED_BRANCHES[@]}"; do
    echo "  - $BRANCH"
  done
  echo ""
  echo "Not: Başarısız brançlar zaten silinmiş olabilir"
fi

echo "=========================================="
