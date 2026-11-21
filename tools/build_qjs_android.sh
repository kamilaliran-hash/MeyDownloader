#!/usr/bin/env bash
# Builds QuickJS-ng (the JavaScript engine yt-dlp needs for YouTube) as a real
# Android arm64 executable, saved as libqjs.so so Android allows running it.
# Usage: ANDROID_NDK_HOME=... tools/build_qjs_android.sh <outdir>
set -euo pipefail
OUT=$(realpath -m "$1"); mkdir -p "$OUT"
WORK=$(mktemp -d); cd "$WORK"
TAG=$(curl -fsSL https://api.github.com/repos/quickjs-ng/quickjs/releases/latest | grep -m1 '"tag_name"' | cut -d'"' -f4)
echo "QuickJS-ng $TAG"
curl -fsSL "https://github.com/quickjs-ng/quickjs/archive/refs/tags/$TAG.tar.gz" | tar -xz
cd quickjs-*
cmake -B build -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_TOOLCHAIN_FILE="$ANDROID_NDK_HOME/build/cmake/android.toolchain.cmake" \
  -DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-24 -DBUILD_SHARED_LIBS=OFF
cmake --build build -j"$(nproc)" --target qjs_exe || cmake --build build -j"$(nproc)"
QJS=$(find build -maxdepth 2 -type f -name qjs | head -1)
"$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip" "$QJS"
cp "$QJS" "$OUT/libqjs.so"
ls -lh "$OUT"
