# 关于
安腾小蝴蝶的全平台认证脚本,以及图形用户界面版本  

## 测试环境
* Mac OS
* Linux
* Windows
* Android
* OpenWrt

## 运行环境
* Python 2.7 Python 3(并未测试)   
* `图形用户界面版本`不需要Python运行环境,适用于Windows、OS X、Linux
* 可能需要的外部依赖性
	- wxpython(GUI) (如果你想自己打包)
	- netifaces(获取指定网卡的IP地址) (目前并不需要)

## AHNU
Linux、MAC OS登录校园网方案:  

* 内网认证使用mentohust  
* 外网用此python脚本

## 其他学校   
已知测试通过的院校:  

* 烟台大学赛尔网
* 广州商学院  
* 广州城建学院
* 辽东学院

## 前排重要提示
仅支持 `BAS认证`,PPPOE、Web认证并不支持  
仅支持 `BAS认证`,PPPOE、Web认证并不支持 X2  
仅支持 `BAS认证`,PPPOE、Web认证并不支持 X3  

> PS: 现在有些客户端版本更新后将BAS认证改名了,有叫`ANSEC`的,还有叫`翼起来`的,本质上还是 `BAS`

## 关于图形用户界面版本
点击[`这里`](https://github.com/lyq1996/an_supplicant/tree/master/gui)查看说明 

## 关于OpenWrt
点击[`这里`](https://github.com/lyq1996/an_supplicant/tree/master/openwrt)查看说明

# 命令行版本:  

## 配置说明:

`esp_config.json`这个文件是用保存配置的

```
{
	"username": "admin",					# 用户名
	"password": "admin",					# 密码
	"auth_host_ip": "210.45.194.10",			# 服务器IP地址(程序自动搜寻不必担心)
	"ip": "8.8.8.8",					# 本机IP地址
	"mac_address": "AA:AA:AA:AA:AA:AA",			# 本机MAC地址
	"client_version": "3.6.4",				# 客户端版本号(推荐3.6.4)
	"service_type": "int",					# 服务类型(程序自动搜寻不必担心)
	"dhcp_setting": "0",					# 开启二次DHCP(0 or 1)
	"delay_enable": "0",					# 延迟上线(等待重新分配IP地址 0 or 1)
	"reconnet_enable": "1",					# 自动重连(0 or 1)
	"message_display_enable": "1"				# 显示认证之后服务器返回的消息(1 or 0)
}
```

## 运行步骤:    

上线:   

```
$ python edu_supplicant.py -c /root/esp_config.json
```

`-c /root/esp_config.json`表示配置文件所在目录

按照提示输入IP、MAC地址等参数,接着程序会自动退出,再次运行即可完成上线

下线: 
``` 
Ctrl ＋ C
```

图:  
![image](/usage.jpg)

## 一些其它事项:   

如果终端显示permission deined:  
```
$ sudo chmod 755 an_supplicant.py
```  

## 参考&鸣谢:  
> [benchmade](https://github.com/gnehsoah/benchmade)  
> [swiftz-protocal](https://github.com/xingrz/swiftz-protocal)
