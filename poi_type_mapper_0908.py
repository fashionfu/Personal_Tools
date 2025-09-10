# -*- coding: utf-8 -*-
"""
POI类型映射脚本 - 0908版本
根据电子地图数据规范样式表，将POI数据的type列内容映射到标准代码
修复了csv模块导入问题和其他编码问题
"""

import os
import pandas as pd
import re
import csv
from typing import Dict, List, Tuple, Optional
from io import StringIO
import difflib

# 配置路径
BASE_DIR = r"E:\demo\数据更改"
POI_FOLDER = os.path.join(BASE_DIR, "333（SJZSJ 333-2025）全国 POI 兴趣点数据分享")
MAPPING_CSV = os.path.join(BASE_DIR, "电子地图样式表0908.csv")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "POI_标准化数据_0908")


class POITypeMapper:
    def __init__(self, mapping_csv_path: str):
        self.mapping_csv_path = mapping_csv_path
        self.code_mapping: Dict[str, Tuple[str, str, str]] = {}  # {中文名: (代码, 英文名, 描述)}
        self.fuzzy_mapping: Dict[str, Tuple[str, str, str]] = {}  # 模糊匹配缓存
        self.load_mapping_data()
    
    def load_mapping_data(self):
        """从规范样式表CSV文件中加载映射数据"""
        if not os.path.exists(self.mapping_csv_path):
            print(f"[ERROR] 映射文件不存在: {self.mapping_csv_path}")
            return
        
        try:
            # 直接读取文件内容并解析
            with open(self.mapping_csv_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            try:
                with open(self.mapping_csv_path, 'r', encoding='gb18030') as f:
                    content = f.read()
            except Exception as e:
                print(f"[ERROR] 无法读取映射文件: {e}")
                return
        
        # 使用正则表达式解析表格格式的映射数据
        # 匹配格式: | 代码 | 英文名称 | 中文名称 |
        pattern = r'\|\s*(\d{4})\s*\|\s*([a-zA-Z][a-zA-Z0-9_]*)\s*,?\s*\|\s*([^,|\n]+?)\s*,?\s*\|'
        matches = re.findall(pattern, content)
        
        for code, en_name, zh_name in matches:
            # 清理中文名称
            zh_name = zh_name.strip()
            en_name = en_name.strip()
            code = code.strip()
            
            # 过滤掉表头和无效数据
            if zh_name and zh_name not in ['代码', '英文名称', '中文名称', '样式推荐类型', '比例尺', '描述']:
                self.code_mapping[zh_name] = (code, en_name, f"{code}|{en_name}|{zh_name}")
                print(f"[DEBUG] 添加映射: {zh_name} -> {code} ({en_name})")
        
        # 额外处理一些特殊格式的数据
        # 匹配另一种格式: 代码,英文名称,中文名称,描述,样式推荐类型
        lines = content.split('\n')
        for line in lines:
            if ',' in line and not line.startswith('|'):
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 3:
                    # 检查第一部分是否为4位代码
                    if parts[0].isdigit() and len(parts[0]) == 4:
                        code = parts[0]
                        en_name = parts[1] if len(parts) > 1 else ""
                        zh_name = parts[2] if len(parts) > 2 else ""
                        
                        if zh_name and zh_name not in ['代码', '英文名称', '中文名称']:
                            self.code_mapping[zh_name] = (code, en_name, f"{code}|{en_name}|{zh_name}")
                            print(f"[DEBUG] 添加映射(CSV格式): {zh_name} -> {code} ({en_name})")
        
        print(f"[INFO] 成功加载 {len(self.code_mapping)} 个映射关系")
        
        # 打印一些示例映射
        if self.code_mapping:
            print("[INFO] 映射示例:")
            count = 0
            for zh_name, (code, en_name, _) in list(self.code_mapping.items())[:5]:
                print(f"  {zh_name} -> {code} ({en_name})")
                count += 1
                if count >= 5:
                    break
    
    def find_best_match(self, poi_type: str, threshold: float = 0.6) -> Optional[Tuple[str, str, str, float]]:
        """使用模糊匹配查找最佳匹配的标准类型"""
        if not poi_type or poi_type.strip() == '':
            return None
        
        poi_type = poi_type.strip()
        
        # 首先尝试精确匹配
        if poi_type in self.code_mapping:
            code, en_name, desc = self.code_mapping[poi_type]
            return (code, en_name, poi_type, 1.0)
        
        # 检查缓存
        if poi_type in self.fuzzy_mapping:
            code, en_name, desc = self.fuzzy_mapping[poi_type]
            return (code, en_name, desc, 0.8)  # 缓存的匹配度设为0.8
        
        # 模糊匹配
        best_match = None
        best_score = 0.0
        
        for std_name in self.code_mapping.keys():
            # 使用不同的匹配策略
            scores = []
            
            # 1. 序列匹配
            seq_score = difflib.SequenceMatcher(None, poi_type, std_name).ratio()
            scores.append(seq_score)
            
            # 2. 包含关系匹配
            if poi_type in std_name or std_name in poi_type:
                contain_score = 0.8
                scores.append(contain_score)
            
            # 3. 关键词匹配
            poi_chars = set(poi_type)
            std_chars = set(std_name)
            if poi_chars & std_chars:  # 有交集
                keyword_score = len(poi_chars & std_chars) / len(poi_chars | std_chars)
                scores.append(keyword_score)
            
            # 取最高分
            max_score = max(scores) if scores else 0.0
            
            if max_score > best_score and max_score >= threshold:
                best_score = max_score
                best_match = (std_name, max_score)
        
        if best_match:
            std_name, score = best_match
            code, en_name, desc = self.code_mapping[std_name]
            # 缓存结果
            self.fuzzy_mapping[poi_type] = (code, en_name, std_name)
            return (code, en_name, std_name, score)
        
        return None
    
    def process_type_hierarchy(self, type_str: str) -> Tuple[str, str, str, float]:
        """处理分层级的类型字符串（用分号分隔）"""
        if pd.isna(type_str) or not type_str:
            return '', '', '', 0.0
        
        # 分割类型层级
        types = [t.strip() for t in str(type_str).replace('；', ';').split(';') if t.strip()]
        
        # 从最具体的类型开始匹配（通常是最后一个）
        for type_item in reversed(types):
            match_result = self.find_best_match(type_item)
            if match_result:
                return match_result
        
        # 如果都没匹配到，返回原始的第一个类型
        first_type = types[0] if types else ''
        return '', '', first_type, 0.0
    
    def try_decode_csv(self, file_path: str) -> Tuple[Optional[pd.DataFrame], str]:
        """尝试用多种编码读取CSV文件"""
        encodings = ['gb18030', 'gbk', 'utf-8', 'utf-8-sig', 'latin1']
        
        for encoding in encodings:
            try:
                # 先读取为字节，再解码
                with open(file_path, 'rb') as f:
                    raw_data = f.read()
                
                text_data = raw_data.decode(encoding)
                
                # 使用更健壮的CSV读取参数
                df = pd.read_csv(
                    StringIO(text_data), 
                    on_bad_lines='skip',
                    quoting=csv.QUOTE_NONE,
                    engine='python'
                )
                return df, encoding
            except Exception as e:
                continue
        
        # 如果所有编码都失败，尝试忽略错误并使用更宽松的参数
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
            text_data = raw_data.decode('gb18030', errors='ignore')
            
            # 使用最宽松的读取参数
            df = pd.read_csv(
                StringIO(text_data), 
                on_bad_lines='skip',
                quoting=csv.QUOTE_NONE,
                engine='python',
                sep=',',
                quotechar='"',
                doublequote=True,
                escapechar='\\'
            )
            return df, 'gb18030-ignore'
        except Exception as e:
            print(f"[ERROR] 无法读取文件 {file_path}: {e}")
            return None, 'failed'
    
    def process_poi_file(self, input_path: str, output_path: str) -> bool:
        """处理单个POI CSV文件"""
        print(f"[INFO] 开始处理文件: {os.path.basename(input_path)}")
        
        # 读取CSV文件
        df, encoding = self.try_decode_csv(input_path)
        if df is None:
            print(f"[ERROR] 无法读取文件: {input_path}")
            return False
        
        print(f"[INFO] 使用编码 {encoding} 成功读取文件，共 {len(df)} 行数据")
        
        # 查找type列
        type_col = None
        for col in df.columns:
            if 'type' in str(col).lower() or '类型' in str(col):
                type_col = col
                break
        
        if type_col is None:
            print(f"[WARN] 未找到type列，跳过文件: {input_path}")
            return False
        
        print(f"[INFO] 找到类型列: {type_col}")
        
        # 处理类型映射
        std_codes = []
        std_names_en = []
        std_names_zh = []
        match_scores = []
        
        for idx, row in df.iterrows():
            type_value = row[type_col]
            code, en_name, zh_name, score = self.process_type_hierarchy(type_value)
            
            std_codes.append(code)
            std_names_en.append(en_name)
            std_names_zh.append(zh_name)
            match_scores.append(score)
            
            # 每1000行打印一次进度
            if (idx + 1) % 1000 == 0:
                print(f"[INFO] 已处理 {idx + 1}/{len(df)} 行")
        
        # 添加新列
        df['std_code'] = std_codes
        df['std_name_en'] = std_names_en
        df['std_name_zh'] = std_names_zh
        df['match_score'] = match_scores
        
        # 保存结果
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"[INFO] 成功保存映射结果: {output_path}")
            
            # 统计映射结果
            mapped_count = sum(1 for score in match_scores if score > 0)
            print(f"[INFO] 映射统计: {mapped_count}/{len(df)} 条记录成功映射 ({mapped_count/len(df)*100:.1f}%)")
            
            return True
        except Exception as e:
            print(f"[ERROR] 保存文件失败: {e}")
            return False
    
    def process_all_poi_files(self, input_folder: str, output_folder: str):
        """处理文件夹中的所有POI CSV文件"""
        if not os.path.exists(input_folder):
            print(f"[ERROR] 输入文件夹不存在: {input_folder}")
            return
        
        # 创建输出文件夹
        os.makedirs(output_folder, exist_ok=True)
        
        # 获取所有CSV文件
        csv_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.csv')]
        
        if not csv_files:
            print(f"[WARN] 在文件夹 {input_folder} 中未找到CSV文件")
            return
        
        print(f"[INFO] 找到 {len(csv_files)} 个CSV文件")
        
        success_count = 0
        for i, filename in enumerate(csv_files, 1):
            print(f"\n[INFO] 处理进度: {i}/{len(csv_files)} - {filename}")
            
            input_path = os.path.join(input_folder, filename)
            # 生成输出文件名
            base_name = os.path.splitext(filename)[0]
            output_filename = f"{base_name}_mapped.csv"
            output_path = os.path.join(output_folder, output_filename)
            
            if self.process_poi_file(input_path, output_path):
                success_count += 1
        
        print(f"\n[INFO] 处理完成！成功处理 {success_count}/{len(csv_files)} 个文件")
        print(f"[INFO] 输出文件夹: {output_folder}")


def main():
    """主函数"""
    print("=== POI类型映射工具 - 0908版本 ===")
    print(f"输入文件夹: {POI_FOLDER}")
    print(f"映射文件: {MAPPING_CSV}")
    print(f"输出文件夹: {OUTPUT_FOLDER}")
    
    # 创建映射器
    mapper = POITypeMapper(MAPPING_CSV)
    
    if not mapper.code_mapping:
        print("[ERROR] 未能加载映射数据，程序退出")
        return
    
    # 处理所有文件
    mapper.process_all_poi_files(POI_FOLDER, OUTPUT_FOLDER)
    
    print("\n=== 处理完成 ===")


if __name__ == "__main__":
    main()

