# 为OpenWrt所写
程序完全由 [`@PrinnyK`](https://github.com/PrinnyK)编写。   
为Openwrt实现安腾`BAS`认证支持

## 特性
* 自动获取活跃的IP和MAC作为运行所需的参数
	- 若失败则报错，你需要自己打开`esp_config.json`填上你的ip和mac
* 自动连接(包含掉线重连和上线失败重连)
* 没有下线功能(`sh stop.sh`之后过几分钟就会掉线)

## 程序依赖
* OpenWrt 15.01(低版本并没测试)
* Python 
* 如若import json 报错则你需要再安装`Python-codecs`这个模块
* 如若import hashlib 报错则你需要再安装`python-openssl`这个模块

# 使用前(请务必仔细阅读)
* 安装OpenWrt 15在你的路由器上(推荐路由器Flash为16M、至少8M，少于8M的请硬改或关闭浏览器)
* 安装Python(各种路由器不一样，自己百度)
* 安装python-codecs、python-openssl、python-logging、python-ctypes

```
opkg update && opkg install python-codecs python-openssl python-logging python-ctypes
```
# 运行步骤
## 修改启动脚本
```
vim start.sh
```
将 
```
python /\*\*\*/edu_supplicant_py.py -c /\*\*\*/esp_config.json>/dev/null &
```  
中的`/\*\*\*/edu_supplicant_py.py` 更改为edu_supplicant_py.py所在的`路径`  
以及`/\*\*\*/esp_config.json` 更改为`esp_config.json`所在的`路径`  

例如
```
python /root/for_example/edu_supplicant_py.py -c /root/for_example/esp_config.json>/dev/null &
echo "edu_supplicant_py start!"

```

## 打开配置文件填入用户名和密码
请勿改变`json`数据交换格式 
 
```
{	
	"password": "123456", 
	"user": "liu", 
	"ip": "",		#可以留空 
	"mac": "",		#可以留空
	"delay": "0"	#延迟上线，等待再次分配ip，可关闭
}
```

## 运行
`***代表目录`
```
cd /***
sh start.sh
```

## 杀死进程
```
cd /***
sh stop.sh
```


## 以输出信息模式运行
```
python /***/edu_supplicant_py -c /***/esp_config.json
```
则会显示与认证相关的信息，方便查看问题出在哪里  
如果报错或者不能认证请移步`issues`反馈