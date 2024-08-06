import streamlit as st
from openai import OpenAI
import time
import re

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Define character and theme options
CHARACTER_OPTIONS = ["貓咪", "狗狗", "花花", "小鳥", "小石頭"]
THEME_OPTIONS = ["親情", "友情", "冒險", "度假", "運動比賽"]

def generate_plot_points(character, theme):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "你是一個創意的故事策劃者。請直接列出3到5個完整的轉折點，每個轉折點應該是一個完整的句子。不要添加編號。"},
            {"role": "user", "content": f"為一個關於{character}的{theme}故事生成3到5個可能的轉折點。確保每個轉折點都是完整的想法。"}
        ],
        max_tokens=300,
        n=1,
        temperature=0.7,
    )
    content = response.choices[0].message.content.strip()
    plot_points = [point.strip() for point in content.split('\n') if point.strip()]
    return plot_points

def generate_story(character, theme, plot_point, pages):
    prompt = f"""
    請你角色扮演成一個暢銷的童書繪本作家，你擅長以孩童的純真眼光看這世界，製作出許多溫暖人心的作品。
    請以下列主題: {theme}發想故事，
    在{pages}的篇幅內，
    說明一個{character}的故事，
    並注意在倒數第三頁加入{plot_point}的元素，
    最後的故事需要是溫馨、快樂的結局。
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "你是一個專業的兒童繪本作家。"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        n=1,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

def generate_pages(story, pages, character, theme, plot_point):
    prompt = f"""
    將以下故事大綱細分至預計{pages}個跨頁的篇幅，每頁需要包括(text, image_prompt)，
    {pages-3}(倒數第三頁)才可以出現{plot_point}的元素，
    在這之前應該要讓{character}的{theme}世界發展故事更多元化:

    {story}

    請確保每頁的格式如下：
    Page X:
    text: [頁面文字]
    image_prompt: [圖像提示]

    不要包含任何其他格式或說明。
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "你是一個專業的繪本編輯。"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        n=1,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

def generate_style_base(story):
    prompt = f"""
    基於以下故事，請思考大方向上你想要呈現的視覺效果，這是你用來統一整體繪本風格的描述，請盡量精簡，使用英文撰寫:

    {story}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "你是一個專業的視覺設計師。"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,
        n=1,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

def image_generation(image_prompt, style_base):
    final_prompt = f"""
    Based on the image prompt: "{image_prompt}" and the style base: "{style_base}",
    please create an image with the following characteristics:
    - Color scheme and background details that match the story's atmosphere
    - Specific style and scene details as described
    - The main character should be prominently featured with the current color, shape, and features
    - Apply at least 3 effect words (lighting effects, color tones, rendering effects, visual style)
    - Use 1 or more composition techniques for visual interest
    - Do not include any text in the image
    - Set a random seed value of 42
    """
    
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=final_prompt,
            n=1,
            size="1792x1024",
            quality="standard",
            response_format="url"
        )
        image_url = response.data[0].url
        return image_url
    except Exception as e:
        st.error(f"生成圖片時發生錯誤: {str(e)}")
        return None

def generate_preview_image():
    with st.spinner("正在生成第一頁預覽圖..."):
        pages = st.session_state.pages_content.split("Page ")
        if len(pages) > 1:
            first_page = pages[1]
            text_parts = first_page.split("text: ")
            if len(text_parts) > 1:
                image_prompt_parts = text_parts[1].split("image_prompt: ")
                if len(image_prompt_parts) > 1:
                    image_prompt = image_prompt_parts[1].strip()
                    image_url = image_generation(image_prompt, st.session_state.style_base)
                    if image_url:
                        st.image(image_url, caption="第一頁預覽")
                        if st.button("重新生成預覽圖"):
                            generate_preview_image()
                    else:
                        st.error("生成預覽圖失敗。請稍後再試。")
                else:
                    st.error("無法找到圖像提示。請檢查生成的內容格式。")
            else:
                st.error("無法找到頁面文字。請檢查生成的內容格式。")
        else:
            st.error("無法找到頁面內容。請檢查生成的內容格式。")

def generate_full_storybook():
    pages = st.session_state.pages_content.split("Page ")[1:]  # 跳過第一個空元素
    total_pages = len(pages)

    # 創建一個進度條
    progress_bar = st.progress(0)

    for i, page in enumerate(pages, 1):
        parts = page.split("text: ")
        if len(parts) > 1:
            text_and_prompt = parts[1].split("image_prompt: ")
            if len(text_and_prompt) > 1:
                text = text_and_prompt[0].strip()
                image_prompt = text_and_prompt[1].strip()
                st.subheader(f"第 {i} 頁")
                st.write(text)
                with st.spinner(f"正在生成第 {i} 頁插圖..."):
                    image_url = image_generation(image_prompt, st.session_state.style_base)
                    if image_url:
                        st.image(image_url, caption=f"第 {i} 頁插圖")
                    else:
                        st.error(f"第 {i} 頁: 生成圖片失敗。請稍後再試。")
                time.sleep(5)  # 添加延遲以避免超過 API 速率限制
            else:
                st.error(f"第 {i} 頁: 無法找到圖像提示。請檢查生成的內容格式。")
        else:
            st.error(f"第 {i} 頁: 無法找到頁面文字。請檢查生成的內容格式。")

        # 更新進度條
        progress_bar.progress(i / total_pages)

    st.success("完整繪本生成完成！")

def main():
    st.title("互動式繪本生成器")

    # 使用 session_state 來保存狀態
    if 'character' not in st.session_state:
        st.session_state.character = None
    if 'theme' not in st.session_state:
        st.session_state.theme = None
    if 'pages' not in st.session_state:
        st.session_state.pages = 8
    if 'plot_points' not in st.session_state:
        st.session_state.plot_points = None
    if 'selected_plot_point' not in st.session_state:
        st.session_state.selected_plot_point = None
    if 'story' not in st.session_state:
        st.session_state.story = None
    if 'pages_content' not in st.session_state:
        st.session_state.pages_content = None
    if 'style_base' not in st.session_state:
        st.session_state.style_base = None

    # 選擇或輸入繪本主角
    character = st.selectbox("選擇繪本主角", CHARACTER_OPTIONS + ["自定義"], key='character_select')
    if character == "自定義":
        character = st.text_input("輸入自定義主角", key='character_input')
    st.session_state.character = character

    # 選擇或輸入繪本主題
    theme = st.selectbox("選擇繪本主題", THEME_OPTIONS + ["自定義"], key='theme_select')
    if theme == "自定義":
        theme = st.text_input("輸入自定義主題", key='theme_input')
    st.session_state.theme = theme

    # 選擇頁數
    st.session_state.pages = st.slider("選擇繪本頁數", 6, 12, st.session_state.pages)

    if st.button("生成故事轉折點"):
        with st.spinner("正在生成故事轉折點..."):
            st.session_state.plot_points = generate_plot_points(st.session_state.character, st.session_state.theme)
        
    if st.session_state.plot_points:
        st.write("生成的故事轉折點：")
        for i, point in enumerate(st.session_state.plot_points, 1):
            st.write(f"{i}. {point}")
        
        st.session_state.selected_plot_point = st.selectbox(
            "選擇故事轉折點",
            options=st.session_state.plot_points + ["自定義"],
            index=0 if st.session_state.selected_plot_point is None else st.session_state.plot_points.index(st.session_state.selected_plot_point) if st.session_state.selected_plot_point in st.session_state.plot_points else len(st.session_state.plot_points),
            format_func=lambda x: x if x != "自定義" else "自定義轉折點",
            key='plot_point_select'
        )
        
        if st.session_state.selected_plot_point == "自定義":
            st.session_state.selected_plot_point = st.text_input("輸入自定義故事轉折點", key='custom_plot_point')

    if st.button("生成繪本"):
        if st.session_state.selected_plot_point:
            with st.spinner("正在生成故事..."):
                st.session_state.story = generate_story(st.session_state.character, st.session_state.theme, st.session_state.selected_plot_point, st.session_state.pages)
                st.write("故事大綱：")
                st.write(st.session_state.story)

                st.session_state.pages_content = generate_pages(st.session_state.story, st.session_state.pages, st.session_state.character, st.session_state.theme, st.session_state.selected_plot_point)
                st.write("分頁內容：")
                st.write(st.session_state.pages_content)

                st.session_state.style_base = generate_style_base(st.session_state.story)
                st.write("風格基礎：")
                st.write(st.session_state.style_base)

            # 生成並顯示第一張圖片
            generate_preview_image()

            if st.button("重新生成繪本劇情"):
                with st.spinner("正在重新生成繪本劇情..."):
                    st.session_state.story = generate_story(st.session_state.character, st.session_state.theme, st.session_state.selected_plot_point, st.session_state.pages)
                    st.session_state.pages_content = generate_pages(st.session_state.story, st.session_state.pages, st.session_state.character, st.session_state.theme, st.session_state.selected_plot_point)
                    st.session_state.style_base = generate_style_base(st.session_state.story)
                    st.experimental_rerun()

            if st.button("生成完整繪本"):
                generate_full_storybook()
        else:
            st.warning("請先選擇或輸入一個故事轉折點。")

if __name__ == "__main__":
    main()
