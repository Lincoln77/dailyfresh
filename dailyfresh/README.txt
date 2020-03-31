项目运行需要环境：
打开celery： celery -A celery_tasks.tasks worker -l info
打开redis: redis-server /etc/redis/redis.conf
打开fastDFS：sudo service fdfs_trackerd start
	     sudo service fdfs_storaged start
打开nginx: sudo /usr/local/nginx/sbin/nginx

