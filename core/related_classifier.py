"""
关联明星推理器
用于从非直接提及明星的标题中，推断最相关的明星人物。
"""
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class RelatedCelebrityClassifier:
    def __init__(self, client, model="deepseek-chat"):
        self.client = client
        self.model = model
    
    def infer_related_celebrity(self, title: str) -> Optional[Dict[str, Any]]:
        """
        分析标题，推断最相关的明星。
        返回一个字典，包含明星姓名和推理原因。
        如果无法推断，则返回None。
        """
        system_prompt = """你是一个精通流行文化和网络热点的分析专家。你的任务是从一个不直接提及真实人物明星的标题中，推断出与之关联最紧密、在网络讨论中热度最高的现实世界明星（演员、导演、歌手、知名公众人物等）。

分析步骤：
1. **理解主题**：识别标题所指的文化产品（电影、电视剧、综艺、书籍）、作品、事件、网络梗或抽象概念。
2. **寻找关联**：思考该主题与哪些现实明星有最强、最直接的创造、表演或所有权关系（如导演、主演、原唱、作者、标志性人物）。
3. **评估热度**：在网络讨论和公众认知中，哪位明星与该主题的绑定程度最深、讨论热度最高。
4. **严格返回格式**：必须且只能返回一个有效的JSON对象。

返回格式：
- 如果可以明确推断出一个关联明星：
{
  “related_celebrity”: “明星姓名”,
  “reasoning”: “简要解释为什么此明星关联度最高（如：'《阿凡达》系列电影的导演'）”
}
- 如果标题是纯节日、普通日常事件或无法推断出明确明星：
{
  “related_celebrity”: null,
  “reasoning”: “解释原因（如：'感恩节是公共节日，无特定关联明星'）”
}

请确保‘related_celebrity’字段只包含人名，不要带称谓和额外说明。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请分析以下标题，并推断最相关的明星：\n标题：{title}"}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={ "type": "json_object" }, # 要求返回结构化JSON
                stream=False
            )
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            # 解析结果
            related_celebrity = result.get("related_celebrity")
            reasoning = result.get("reasoning", "无说明")
            
            if related_celebrity:
                logger.info(f"标题 ‘{title}’ 的关联明星推断为: {related_celebrity}， 原因: {reasoning}")
                return {
                    "name": related_celebrity,
                    "original_title": title,
                    "reasoning": reasoning,
                    "type": "related" # 标记为关联推断结果
                }
            else:
                logger.info(f"标题 ‘{title}’ 未推断出明确关联明星。原因: {reasoning}")
                return None
                
        except json.JSONDecodeError:
            logger.error(f"解析关联明星推断的JSON响应失败。原始响应: {result_text}")
            return None
        except Exception as e:
            logger.error(f"关联明星推断API调用失败: {e}")
            return None