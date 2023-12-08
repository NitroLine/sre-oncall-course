config_path="balancer/configs/nginx.conf"
sed -i "s/oncall:8080/oncall:8080 down/" "$config_path";
docker exec -it sre-oncall-course-balancer-1 nginx -s reload;
docker compose down oncall-web;
docker compose up oncall-web -d --build;
sed -i "s/ down//" "$config_path";
sed -i "s/oncall2:8080/oncall2:8080 down/" "$config_path";
docker exec -it sre-oncall-course-balancer-1 nginx -s reload;
docker compose down oncall-web-2;
docker compose up oncall-web-2 -d --build;
sed -i "s/ down//" "$config_path";
docker exec -it sre-oncall-course-balancer-1 nginx -s reload;