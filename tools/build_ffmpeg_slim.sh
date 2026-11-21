#!/usr/bin/env bash
# Builds a SLIM ffmpeg containing only what MeyDownloader uses:
#   - MP3 conversion  (decode aac/opus/vorbis/mp3/flac -> encode with LAME)
#   - MP4 merge/remux (stream copy of h264/hevc/vp9/av1 + aac/opus, no re-encoding)
#   - metadata/chapters, HLS fixups
# Video is never re-encoded, so dropping all other codecs costs no speed.
# Result: ~3-6 MB instead of ~80-130 MB.
#
# Usage:  tools/build_ffmpeg_slim.sh android <outdir>   (needs ANDROID_NDK_HOME)
#         tools/build_ffmpeg_slim.sh windows <outdir>   (needs mingw-w64, nasm)
set -euo pipefail
TARGET=$1
OUT=$(realpath -m "$2")
FFMPEG_VER=7.1.1
LAME_VER=3.100
WORK=$(mktemp -d)
PREFIX=$WORK/prefix
mkdir -p "$OUT" "$PREFIX"
cd "$WORK"

curl -fsSL "https://ffmpeg.org/releases/ffmpeg-$FFMPEG_VER.tar.xz" | tar -xJ
curl -fsSL "https://downloads.sourceforge.net/project/lame/lame/$LAME_VER/lame-$LAME_VER.tar.gz" | tar -xz
# lame 3.100 exports a symbol that no longer exists; drop it so linking works
sed -i '/lame_init_old/d' lame-$LAME_VER/include/libmp3lame.sym

if [ "$TARGET" = android ]; then
  API=24
  TC=$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin
  export CC=$TC/aarch64-linux-android$API-clang CXX=$TC/aarch64-linux-android$API-clang++
  export AR=$TC/llvm-ar RANLIB=$TC/llvm-ranlib STRIP=$TC/llvm-strip
  LAME_HOST=aarch64-linux-android
  FF_CROSS=(--target-os=android --arch=aarch64 --enable-cross-compile
            --cc="$CC" --cxx="$CXX" --ar="$AR" --ranlib="$RANLIB" --strip="$STRIP"
            --nm="$TC/llvm-nm" --enable-pic --enable-neon)
  FF_EXTRA_LD=""
  PROGRAMS=(--enable-ffmpeg)
else
  LAME_HOST=x86_64-w64-mingw32
  export CC=x86_64-w64-mingw32-gcc
  FF_CROSS=(--target-os=mingw32 --arch=x86_64 --enable-cross-compile
            --cross-prefix=x86_64-w64-mingw32-)
  FF_EXTRA_LD="-static -static-libgcc"
  PROGRAMS=(--enable-ffmpeg --enable-ffprobe)
fi

# ---- LAME (MP3 encoder)
( cd lame-$LAME_VER
  ./configure --host=$LAME_HOST --prefix="$PREFIX" --disable-shared --enable-static \
              --disable-frontend --disable-decoder CFLAGS="-O2"
  make -j"$(nproc)" && make install )

# ---- ffmpeg (only the parts we need)
( cd ffmpeg-$FFMPEG_VER
  ./configure "${FF_CROSS[@]}" \
    --prefix="$PREFIX" \
    --pkg-config-flags=--static \
    --extra-cflags="-I$PREFIX/include -O2" \
    --extra-ldflags="-L$PREFIX/lib $FF_EXTRA_LD" \
    --disable-everything --disable-autodetect --disable-doc --disable-debug \
    --disable-network --disable-shared --enable-static \
    --disable-programs "${PROGRAMS[@]}" \
    --disable-avdevice --disable-swscale --disable-postproc \
    --enable-swresample --enable-avfilter \
    --enable-libmp3lame \
    --enable-protocol=file,pipe \
    --enable-demuxer=mov,matroska,mp3,aac,ogg,flac,wav,flv,mpegts,ffmetadata,concat,m4v,h264,hevc \
    --enable-muxer=mp4,mov,ipod,mp3,matroska,webm,adts,ogg,opus,flac,ffmetadata,null \
    --enable-decoder=aac,aac_latm,mp3,mp3float,opus,vorbis,flac,alac,pcm_s16le,pcm_f32le \
    --enable-encoder=libmp3lame \
    --enable-parser=aac,aac_latm,h264,hevc,vp8,vp9,av1,opus,vorbis,mpegaudio,flac \
    --enable-bsf=aac_adtstoasc,h264_mp4toannexb,hevc_mp4toannexb,extract_extradata,vp9_superframe,vp9_superframe_split,av1_frame_merge,av1_frame_split,null \
    --enable-filter=aresample,aformat,anull,null,format,abuffer,abuffersink,buffer,buffersink,volume,atrim,trim,copy,acopy
  make -j"$(nproc)" )

if [ "$TARGET" = android ]; then
  "$STRIP" ffmpeg-$FFMPEG_VER/ffmpeg
  cp ffmpeg-$FFMPEG_VER/ffmpeg "$OUT/libffmpeg.so"
else
  x86_64-w64-mingw32-strip ffmpeg-$FFMPEG_VER/ffmpeg.exe ffmpeg-$FFMPEG_VER/ffprobe.exe
  cp ffmpeg-$FFMPEG_VER/ffmpeg.exe ffmpeg-$FFMPEG_VER/ffprobe.exe "$OUT/"
fi
ls -lh "$OUT"
