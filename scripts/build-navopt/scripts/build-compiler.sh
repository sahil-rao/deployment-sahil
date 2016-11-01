#!/bin/bash

set -eux

BRANCH=$1

git -C /gitcache/compiler archive $BRANCH | tar -x

echo "--- building compiler..."
mvn package -DskipTests

echo "--- archiving compiler..."
mkdir baaz_compiler

cp target/Baaz-Compiler-1/*.jar baaz_compiler/
cp target/classes/logback.xml baaz_compiler/
tar -zcvf /target/Baaz-Compiler.tar.gz baaz_compiler
