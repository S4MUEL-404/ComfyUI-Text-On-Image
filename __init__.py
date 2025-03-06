import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import torch

class TextOnImage:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        # 定义字体文件目录
        font_dir = os.path.join(os.path.dirname(__file__), "font")
        # 获取目录下所有 .ttc 和 .ttf 文件
        font_files = [f for f in os.listdir(font_dir) if f.endswith(('.ttc', '.ttf'))]
        # 如果目录为空，默认提供一个占位选项
        if not font_files:
            font_files = ["default"]

        return {
            "required": {
                "text": ("STRING", {
                    "default": "",
                    "multiline": True,
                }),
                "image": ("IMAGE",),
                "x": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 4096,
                    "step": 1,
                    "display": "number",
                }),
                "y": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 4096,
                    "step": 1,
                    "display": "number",
                }),
                "font_size": ("INT", {
                    "default": 12,
                    "min": 0,
                    "max": 320,
                    "step": 1,
                    "display": "number",
                }),
                "text_color": ("STRING", {
                    "default": "#ffffff",
                }),
                "shadow_x": ("INT", {
                    "default": 0,
                    "min": -100,
                    "max": 100,
                    "step": 1,
                    "display": "number",
                }),
                "shadow_y": ("INT", {
                    "default": 0,
                    "min": -100,
                    "max": 100,
                    "step": 1,
                    "display": "number",
                }),
                "shadow_color": ("STRING", {
                    "default": "none",
                }),
                "font_file": (font_files, {
                    "default": font_files[0],  # 默认选择第一个字体文件
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "apply_text"
    CATEGORY = "💀Text On Image"

    def hex_to_rgb(self, hex_color):
        """将 HEX 色值转换为 RGB 元组"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def apply_text(self, text, image, x, y, font_size, text_color, shadow_x, shadow_y, shadow_color, font_file):
        if text == "":
            return (image,)

        # 将输入的 torch.Tensor 转换为 PIL 图像
        img = image[0].cpu().numpy()  # 形状为 (H, W, C)
        img = (img * 255).astype(np.uint8)  # 转换为 [0,255] 的 uint8 类型
        img = Image.fromarray(img)  # 转换为 PIL.Image

        # 构建字体文件路径
        font_dir = os.path.join(os.path.dirname(__file__), "font")
        font_path = os.path.join(font_dir, font_file)

        # 加载字体
        try:
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            font = ImageFont.load_default()  # 如果字体加载失败，使用默认字体

        # 转换颜色
        text_color_rgb = self.hex_to_rgb(text_color)
        shadow_color_rgb = None if shadow_color == "none" else self.hex_to_rgb(shadow_color)

        # 在图片上绘制文字
        draw = ImageDraw.Draw(img)

        # 如果有投影，先绘制投影文字
        if shadow_color_rgb:
            shadow_position = (x + shadow_x, y + shadow_y)
            draw.text(shadow_position, text, font=font, fill=shadow_color_rgb)

        # 绘制实际文字
        draw.text((x, y), text, font=font, fill=text_color_rgb)

        # 将 PIL.Image 转换回 torch.Tensor
        img = np.array(img).astype(np.float32) / 255.0  # 转换为 [0,1] 的 float32 类型
        img = torch.from_numpy(img)[None,]  # 添加批次维度，形状为 (1, H, W, C)

        return (img,)

# 注册节点
NODE_CLASS_MAPPINGS = {
    "TextOnImage": TextOnImage
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextOnImage": "💀Text On Image"
}