#!/bin/bash
set -e

mkdir -p /data /home/testuser/projects

create_files() {
    local dir=$1
    local count=$2
    local size=$3
    
    mkdir -p "$dir"
    for i in $(seq 1 $count); do
        dd if=/dev/urandom of="$dir/file_$i.dat" bs=1K count=$size 2>/dev/null
    done
}

create_old_files() {
    local dir=$1
    local count=$2
    local size=$3
    local days=$4
    
    mkdir -p "$dir"
    for i in $(seq 1 $count); do
        dd if=/dev/urandom of="$dir/old_file_$i.dat" bs=1K count=$size 2>/dev/null
        touch -d "$days days ago" "$dir/old_file_$i.dat"
    done
}

create_files /data/app_logs 50 100
create_files /data/app_logs/archive 20 500

create_old_files /data/backup/2024 30 200 400

create_files /data/database/main 5 50
mkdir -p /data/database/indexes
create_files /data/database/indexes/idx1 100 10
create_files /data/database/indexes/idx2 80 15

create_files /data/cache 200 5
create_old_files /data/cache/old 50 20 180

create_files /home/testuser/projects/app1/src 30 10
create_files /home/testuser/projects/app1/build 100 50
create_old_files /home/testuser/projects/app1/build/cache 40 30 120

create_files /home/testuser/projects/app2/src 20 15
create_files /home/testuser/projects/app2/logs 60 80

mkdir -p /home/testuser/documents
create_files /home/testuser/documents 10 100
create_old_files /home/testuser/documents/archive 25 200 500

chown -R testuser:testuser /home/testuser
chmod -R 755 /data

echo "Dane testowe zostały wygenerowane!"
du -sh /data /home/testuser
