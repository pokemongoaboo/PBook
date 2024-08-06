import streamlit as st
from openai import OpenAI
import time
import random

# 设置OpenAI客户端
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def generate_story(character, theme, twist, pages):
    # 使用OpenAI的GPT模型生成故事
    prompt = f"""
    请你角色扮演成一个暢銷的童書繪本作家，你擅長以孩童的純真眼光看這世界，製作出許多溫暖人心的作品。
    請以下列主題: {theme} 發想故事，
    在 {pages} 的篇幅內，
    說明一個 {character} 的故事，
    並注意在倒數第三頁加入 {twist} 的元素，
    最後的故事需要是溫馨、快樂的結局。
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # 使用您确认可用的模型
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content

def generate_page_prompts(story, pages, character, theme, twist):
    prompt = f"""
    將以下故事大綱細分至預計 {pages} 個跨頁的篇幅，每頁需要包括(text，image_prompt)，
    {pages-3}(倒數第三頁)才可以出現 {twist}，
    在這之前應該要讓 {character} 的 {theme} 世界發展故事更多元化：
    
    {story}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # 使用您确认可用的模型
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content

def generate_style_base(story):
    prompt = f"""
    基于以下故事，请思考大方向上你想要呈现的视觉效果，这是你用来统一整体绘本风格的描述，请尽量精简，使用英文撰写：
    
    {story}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # 使用您确认可用的模型
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content

def generate_image(image_prompt, style_base):
    final_prompt = f"""
    根据以下内容补充色调、背景描述、具体风格、画面细节，以及角色目前的颜色、型体、特征。
    必须具体的描述，同时至少3个效果词(光照效果、色彩色调、渲染效果、视觉风格)和1个以上的构图技巧，以构成完整的prompt。
    请设定随机种子值为42，且不要有文字出现在图中，使用英文撰写：
    
    Image prompt: {image_prompt}
    Style base: {style_base}
    """
    
    response = client.images.generate(
        model="dall-e-3",
        prompt=final_prompt,
        n=1,
        size="1792x1024"
    )
    
    return response.data[0].url

def main():
    st.title("交互式儿童绘本生成器")
    
    # 选择或输入绘本主角
    character_options = ["貓咪", "狗狗", "花花", "小鳥", "小石頭"]
    character = st.selectbox("选择绘本主角", character_options + ["其他"])
    if character == "其他":
        character = st.text_input("输入自定义主角")
    
    # 选择或输入绘本主题
    theme_options = ["親情", "友情", "冒險", "度假", "運動比賽"]
    theme = st.selectbox("选择绘本主题", theme_options + ["其他"])
    if theme == "其他":
        theme = st.text_input("输入自定义主题")
    
    # 选择页数
    pages = st.slider("选择绘本页数", 6, 12)
    
    if st.button("生成故事框架"):
        # 生成初步故事
        story = generate_story(character, theme, "", pages)
        st.session_state.story = story
        st.write("初步故事框架已生成。")
        
        # 生成故事转折点选项
        twist_options = generate_twist_options(story)
        st.session_state.twist_options = twist_options
        
        # 让用户选择转折点
        twist = st.radio("选择故事转折重点", twist_options + ["其他"])
        if twist == "其他":
            twist = st.text_input("输入自定义转折重点")
        
        if st.button("确认转折点并生成完整故事"):
            # 重新生成带有转折点的完整故事
            full_story = generate_story(character, theme, twist, pages)
            st.session_state.full_story = full_story
            
            # 生成分页提示词
            page_prompts = generate_page_prompts(full_story, pages, character, theme, twist)
            st.session_state.page_prompts = page_prompts
            
            # 生成风格基础
            style_base = generate_style_base(full_story)
            st.session_state.style_base = style_base
            
            st.write("完整故事和图像提示词已生成。")
            st.write("故事预览：")
            st.write(full_story)
            
            if st.button("生成第一张图像"):
                # 解析第一页的图像提示词
                first_page_prompt = page_prompts.split("\n")[0]  # 这里需要根据实际输出格式进行调整
                image_url = generate_image(first_page_prompt, style_base)
                st.image(image_url)
                
                if st.button("确认并生成完整绘本"):
                    # 这里需要循环生成所有页面的图像
                    for i, page_prompt in enumerate(page_prompts.split("\n")):
                        image_url = generate_image(page_prompt, style_base)
                        st.write(f"第 {i+1} 页")
                        st.image(image_url)
                        st.write(page_prompt)
                        time.sleep(5)  # 添加延迟以避免API限制

def generate_twist_options(story):
    # 使用OpenAI的GPT模型生成转折点选项
    prompt = f"""
    根据以下故事，生成3到5个可能的故事转折重点选项：
    
    {story}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # 使用您确认可用的模型
        messages=[{"role": "user", "content": prompt}]
    )
    
    options = response.choices[0].message.content.split("\n")
    return [option.strip() for option in options if option.strip()]

if __name__ == "__main__":
    main()
