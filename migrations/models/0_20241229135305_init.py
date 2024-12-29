from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "devicemessage" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL /* 主键id */,
    "device_addr" VARCHAR(20)   /* 设备IP地址 */,
    "message_source" INT   /* 信息来源 0=未知 1=车位相机 2=通道相机 3=LED网络屏 4=LCD一体屏 5=Lora节点 6=四字节节点 */,
    "message" VARCHAR(1000)   /* 接收的服务器下发指令 */,
    "create_time" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP /* 创建时间 */,
    "update_time" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP /* 更新时间 */
) /* 设备信息表 */;
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
