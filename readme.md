# poe逆向

### 使用方法

``` 
git clone         
```

```  cd  poepoe  ``` ```  vi config.py  ``` 修改配置文件

``` 
docker build -t oppoe:latest .
```
``` 
docker run -p 47124:47124  -v /root/config.py:config.py  -d oppoe:latest
```
使用

1、（可选操作）使用宝塔反代，使用nginx反代 创建一个web站点--(例如：a.example.com)，使用反向代理，反向代理地址为：http://127.0.0.1:47124

2、使用aichat，添加baseurl，地址为刚刚自己创建的web站点.(和第一步的web站点对应 http://a.example.com)

如果第一步没有使用反向代理，那么此处的baseurl地址为：http://IP:47124 （IP为服务器的公网IP）

3、直接使用： 新增模型，可以实现对应的不同效果

模型名为config文件中poe_bot的模型名。

4、apikey：填写config文件中poe_apikey。默认为sk-x1OQLM4bQYx8tT3BlbkFJuev