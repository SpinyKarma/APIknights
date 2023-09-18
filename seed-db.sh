#!/bin/bash

# for file in "./src/db"/*.sql; do
#     psql -f "${file}" > ${file%.sql}.txt
# done

psql -f ./src/db/setup-db.sql > ./src/db/setup-db.txt