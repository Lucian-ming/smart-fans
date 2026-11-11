# TB6612 公开原生工程获取记录

## 结果
没有取得可用焊盘坐标或网络映射。本轮不能确认用户实物为15.24mm排距，不修改设计。

## 已取得的公开证据
- [江协复刻工程](https://oshwhub.com/zanfi1010/pid-ru-men-tao-jian-pcb-ban-fu-ke-jiang-xie-ke-ji)：SSR工程UUID `1a8334bff644402591ee851ed35f6164`，origin=pro。原生编辑器入口为 https://pro.lceda.cn/editor#id=1a8334bff644402591ee851ed35f6164 。
- [在线PID底板](https://oshwhub.com/id_shift/pid-dian-ji-kong-zhi-_-zai-xian)：SSR工程UUID `6af32f99ba774cdfa2778fb8da9a823b`，origin=pro。原生入口为 https://pro.lceda.cn/editor#id=6af32f99ba774cdfa2778fb8da9a823b 。
- 两者SSR `attachments=[]`、`version_documents=[]`。这仅表示返回的页面没有附件，不证明服务器没有原生工程。
- 公开页面前端 `page-88b84aaa6eddba46.js` module24945定义GET `/api/project/{uuid}`、GET `/api/project/{uuid}/proImages`；调用处消费boards、pcb_info、documents等字段。脚本保存在同目录tb6612_web_sources。

## 获取阻断
2026-11-04 17:48向oshwhub.com发送上述两个工程的detail/proImages四个公开GET请求，全部返回HTTP418，CloudWAF正文“访问被拦截！您的请求疑似攻击行为！”。未返回工程JSON。没有尝试认证绕过、代理、Cookie伪造或访问私有工程。

原始响应保存于tb6612_web_sources/same_detail.json、same_images.json、clone_detail.json、clone_images.json；扩展名虽为json，内容实际是418 HTML，不得当工程数据解析。获取脚本get_tb_projects.py退出0只代表请求脚本完成，不代表工程获取成功。

## 最快可靠下一步
若用户可正常在浏览器打开上述原生编辑链接，导出工程/PCB文件到工作区，再解析模块孔位、排距、网络及安装面。若无法取得，实测两排中心距并提供安装面清楚的针序照片。2.50/2.54两针成形容忍不能授权整排或镜像猜测。
