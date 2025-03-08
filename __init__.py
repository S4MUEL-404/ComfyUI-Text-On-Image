import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import torch
import logging
import math

class TextOnImage:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        font_dir = os.path.join(os.path.dirname(__file__), "font")
        font_files = [f for f in os.listdir(font_dir) if f.endswith(('.ttc', '.ttf'))]
        if not font_files:
            font_files = ["default"]

        return {
            "required": {
                "text": ("STRING", {"default": "", "multiline": True}),
                "image": ("IMAGE",),
                "x": ("INT", {"default": 0, "min": 0, "max": 4096, "step": 1}),
                "y": ("INT", {"default": 0, "min": 0, "max": 4096, "step": 1}),
                "font_size": ("INT", {"default": 12, "min": 0, "max": 320, "step": 1}),
                "text_color": ("STRING", {"default": "#ffffff"}),
                "text_opacity": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "use_gradient": ("BOOLEAN", {"default": False}),
                "start_color": ("STRING", {"default": "#ff0000"}),
                "end_color": ("STRING", {"default": "#0000ff"}),
                "angle": ("INT", {"default": 0, "min": -180, "max": 180, "step": 1}),
                "stroke_width": ("INT", {"default": 0, "min": 0, "max": 100, "step": 1}),
                "stroke_color": ("STRING", {"default": "#000000"}),
                "stroke_opacity": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "shadow_x": ("INT", {"default": 0, "min": -100, "max": 100, "step": 1}),
                "shadow_y": ("INT", {"default": 0, "min": -100, "max": 100, "step": 1}),
                "shadow_color": ("STRING", {"default": "#000000"}),
                "shadow_opacity": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "font_file": (font_files, {"default": font_files[0]}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "apply_text"
    CATEGORY = "💀Text On Image"

    def hex_to_rgb(self, hex_color):
        """将 HEX 色值转换为 RGB 元组"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def create_gradient(self, width, height, start_color_rgb, end_color_rgb, angle):
        """创建渐变图像"""
        # 创建一个空白的 RGBA 图像
        gradient_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(gradient_img)

        # 计算渐变方向
        rad = math.radians(angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        # 确定渐变方向上的投影长度
        proj_width = abs(width * cos_a) + abs(height * sin_a)
        proj_height = abs(width * sin_a) + abs(height * cos_a)
        length = max(proj_width, proj_height)

        if length == 0:
            length = 1  # 防止除以零

        # 遍历图像的每个像素，计算其在渐变方向上的投影位置
        for x in range(width):
            for y in range(height):
                # 计算当前点在渐变方向上的投影距离
                t = (x * cos_a + y * sin_a + length / 2) / length
                t = max(0, min(1, t))  # 限制 t 在 [0, 1] 范围内

                # 插值计算颜色
                r = int(start_color_rgb[0] + (end_color_rgb[0] - start_color_rgb[0]) * t)
                g = int(start_color_rgb[1] + (end_color_rgb[1] - start_color_rgb[1]) * t)
                b = int(start_color_rgb[2] + (end_color_rgb[2] - start_color_rgb[2]) * t)
                draw.point((x, y), fill=(r, g, b, 255))

        return gradient_img

    def apply_text(self, text, image, x, y, font_size, text_color, text_opacity,
                  stroke_width, stroke_color, stroke_opacity,
                  shadow_x, shadow_y, shadow_color, shadow_opacity,
                  font_file, use_gradient, start_color, end_color, angle):
        if text == "":
            logging.info("Text is empty, returning original image.")
            return (image,)

        # 将输入的 torch.Tensor 转换为 PIL 图像
        img = image[0].cpu().numpy()
        img = (img * 255).astype(np.uint8)
        base_img = Image.fromarray(img).convert('RGBA')
        img_width, img_height = base_img.size
        logging.info(f"Image size: {img_width}x{img_height}")

        # 构建字体文件路径
        font_dir = os.path.join(os.path.dirname(__file__), "font")
        font_path = os.path.join(font_dir, font_file)
        logging.info(f"Font path: {font_path}")

        # 加载字体
        try:
            font = ImageFont.truetype(font_path, font_size)
            logging.info(f"Font loaded successfully: {font_path}")
        except IOError as e:
            logging.warning(f"Failed to load font {font_path}: {e}, using default font.")
            font = ImageFont.load_default()

        # 转换颜色
        text_color_rgb = self.hex_to_rgb(text_color)
        stroke_color_rgb = self.hex_to_rgb(stroke_color)
        shadow_color_rgb = None if shadow_color == "none" else self.hex_to_rgb(shadow_color)
        start_color_rgb = self.hex_to_rgb(start_color)
        end_color_rgb = self.hex_to_rgb(end_color)

        # 使用 ImageDraw.textbbox 精确计算文字区域
        temp_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        text_bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # 增加安全高度
        safety_margin = font_size // 2
        text_height += safety_margin

        logging.info(f"Text dimensions: width={text_width}, height={text_height}")

        # 计算总padding（包括描边和投影）
        padding = max(stroke_width * 2, abs(shadow_x), abs(shadow_y))

        # 调整文字位置
        text_left = max(0, x - padding)
        text_top = max(0, y - padding)
        text_right = min(img_width, x + text_width + padding)
        text_bottom = min(img_height, y + text_height + padding)

        # 如果文字超出图像底部，向上调整
        if text_bottom > img_height:
            offset = text_bottom - img_height
            text_top = max(0, text_top - offset)
            text_bottom = img_height

        logging.info(f"Canvas bounds: left={text_left}, top={text_top}, right={text_right}, bottom={text_bottom}")

        # 创建文字层
        canvas_width = text_right - text_left
        canvas_height = text_bottom - text_top
        if canvas_width <= 0 or canvas_height <= 0:
            logging.warning("Canvas dimensions are invalid, returning original image.")
            return (image,)
        canvas = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
        canvas_draw = ImageDraw.Draw(canvas)
        logging.info(f"Canvas created: {canvas_width}x{canvas_height}")

        # 计算文字在画布中的相对位置（y 作为顶部位置）
        relative_x = x - text_left
        relative_y = y - text_top
        logging.info(f"Relative text position: x={relative_x}, y={relative_y}")

        # 绘制投影
        if shadow_color_rgb and (shadow_x != 0 or shadow_y != 0):
            try:
                shadow_pos = (relative_x + shadow_x, relative_y + shadow_y)
                canvas_draw.text(shadow_pos, text, font=font, 
                               fill=shadow_color_rgb + (int(255 * shadow_opacity),))
                logging.info("Shadow drawn successfully.")
            except Exception as e:
                logging.error(f"Failed to draw shadow: {e}")

        # 绘制描边
        if stroke_width > 0:
            try:
                for dx in range(-stroke_width, stroke_width + 1):
                    for dy in range(-stroke_width, stroke_width + 1):
                        if dx != 0 or dy != 0:
                            stroke_pos = (relative_x + dx, relative_y + dy)
                            canvas_draw.text(stroke_pos, text, font=font, 
                                           fill=stroke_color_rgb + (int(255 * stroke_opacity),))
                logging.info(f"Stroke drawn with width {stroke_width}.")
            except Exception as e:
                logging.error(f"Failed to draw stroke: {e}")

        # 绘制主文字
        try:
            if use_gradient:
                # 创建渐变图像
                gradient_img = self.create_gradient(text_width, text_height, start_color_rgb, end_color_rgb, angle)
                
                # 创建文字蒙版
                text_mask = Image.new('L', (text_width, text_height), 0)
                mask_draw = ImageDraw.Draw(text_mask)
                mask_draw.text((0, 0), text, font=font, fill=255)
                
                # 将渐变应用到文字上
                gradient_text = Image.new('RGBA', (text_width, text_height), (0, 0, 0, 0))
                gradient_text.paste(gradient_img, (0, 0), text_mask)
                
                # 应用透明度
                gradient_text_data = np.array(gradient_text)
                gradient_text_data[..., 3] = (gradient_text_data[..., 3] * text_opacity).astype(np.uint8)
                gradient_text = Image.fromarray(gradient_text_data)
                
                # 将渐变文字粘贴到画布上
                canvas.paste(gradient_text, (relative_x, relative_y), gradient_text)
            else:
                # 使用单一颜色绘制文字
                canvas_draw.text((relative_x, relative_y), text, font=font, 
                               fill=text_color_rgb + (int(255 * text_opacity),))
            logging.info("Main text drawn successfully.")
        except Exception as e:
            logging.error(f"Failed to draw main text: {e}")
            return (image,)

        # 将文字画布粘贴到主图像上
        try:
            base_img.paste(canvas, (text_left, text_top), canvas)
            logging.info("Canvas pasted to base image successfully.")
        except Exception as e:
            logging.error(f"Failed to paste canvas to base image: {e}")
            return (image,)

        # 将 PIL.Image 转换回 torch.Tensor
        img = np.array(base_img).astype(np.float32) / 255.0
        img = torch.from_numpy(img)[None,]
        logging.info("Image converted back to tensor.")

        return (img,)

# 注册节点
NODE_CLASS_MAPPINGS = {
    "TextOnImage": TextOnImage
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextOnImage": "💀Text On Image"
}
