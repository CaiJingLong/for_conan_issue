# Export all dependencies

WorkDir=$(readlink -f $(dirname $0))

export_lib() {
    if [ -z "$1" ]; then
        echo "ERROR: export_lib: missing argument for profile"
        exit 1
    fi

    export OUTPUT_LIB_DIR="$WorkDir/build/$1"

    profile=$1

    export OUTPUT_LIB_DIR=build/install/$profile
    echo "profile: $profile"
    echo "OUTPUT_LIB_DIR: $OUTPUT_LIB_DIR"

    conan create . --build=missing -pr:b=./default -pr:h=./$profile
}

export_lib android-v8
