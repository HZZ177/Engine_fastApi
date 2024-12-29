import tortoise
import uvicorn
from fastapi import FastAPI
from apps.lora_node.urls import lora_router
from apps.channel_camera.urls import channel_camera_router
from apps.four_bytes_node.urls import four_bytes_node_router
from apps.parking_camera.urls import parking_camera_router
from apps.network_led.urls import network_led_router
from apps.network_lcd.urls import network_lcd_router
from core.events import register_startup_and_shutdown_events
from core.middleware import RequestLoggingMiddleware
from tortoise.contrib.fastapi import register_tortoise
from core.settings import TORTOISE_ORM

# 初始化FastAPI实例
app = FastAPI()

# 注册框架启动和关闭事件，传入FastAPI实例
register_startup_and_shutdown_events(app)

# 注册中间件
app.add_middleware(RequestLoggingMiddleware)    # 日志记录每个请求信息

# 注册tortoise
register_tortoise(app, config=TORTOISE_ORM)

# 注册路由
app.include_router(lora_router, prefix="/lora_node", tags=["lora节点相关接口"])
app.include_router(channel_camera_router, prefix="/channel_camera", tags=["通道相机相关接口"])
app.include_router(four_bytes_node_router, prefix="/four_bytes_node", tags=["四字节网络节点相关接口"])
app.include_router(parking_camera_router, prefix="/parking_camera", tags=["车位相机相关接口"])
app.include_router(network_led_router, prefix="/network_led", tags=["LED网络屏相关接口"])
app.include_router(network_lcd_router, prefix="/network_lcd", tags=["LCD一体屏相关接口"])
#

if __name__ == "__main__":
    uvicorn.run(app="main:app", host="127.0.0.1", port=8000, reload=True)
