# dailyfresh
Django项目Dailyfresh-基于B2C的天天生鲜商城
## 项目需要的环境的安装包存放在environment目录下
python的所有依赖可在虚拟环境下使用`pip install -r requirements.txt`
## 技术栈
•	语言：Python3.* (Django1.8.2)
•	数据库: MySql、 redis
•	任务队列(异步处理): celery 4.1.1(django-celery)
•	分布式文件存储: FastDFS
•	搜索引擎(商品检索)： haystack 2.6.1(django-haystack)、whoosh、二次开发
•	web服务器配置: Nginx+ uwsgi
•	开发环境： PyCharm、Linux、vim
## 项目总结
1.	生鲜类产品  B2C  PC电脑端网页
2.	功能模块：用户模块  商品模块（首页、 搜索、商品） 购物车模块  订单模块（下单、 支付）
3.	用户模块：**注册、登录、激活、退出**、个人中心、地址
4.	商品模块：**首页**、详情、列表、**搜索（haystack+whoosh）**
5.	购物车： **增加、删除、修改、查询**
6.	订单模块：确认订单页面、**提交订单（下单）、请求支付、查询支付结果**、评论
7.	django默认的认证系统 **AbstractUser**
8.	itsdangerous  生成签名的token （序列化工具 dumps  loads）
9.	邮件 （django提供邮件支持 配置参数  send_mail）
10.	 **celery (重点**  整体认识 异步任务)
11.	 **页面静态化** （缓解压力  celery  nginx）
12.	 **缓存**（缓解压力， 保存的位置、有效期、与数据库的一致性问题）
13.	 FastDFS (分布式的图片存储服务， 修改了django的默认文件存储系统)
14.	 搜索（ whoosh  索引  分词）
15.	 **购物车** redis 哈希 **历史记录** redis list
16.	 ajax 前端用ajax请求后端接口
17.	 事务
18.	 高并发的库存问题 （**悲观锁、乐观锁**）
19.	 **支付的使用流程**
20.	 nginx （负载均衡  提供静态文件）
