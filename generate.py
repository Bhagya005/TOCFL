import pandas as pd


def main():
    # Load Excel
    file_path = "CCCC_Vocabulary_2022.xlsx"
    df = pd.read_excel(file_path)

    # Create columns if they don't exist
    if "Example" not in df.columns:
        df["Example"] = ""
    if "Example Pinyin" not in df.columns:
        df["Example Pinyin"] = ""
    if "Example Meaning" not in df.columns:
        df["Example Meaning"] = ""

    # Example dictionary
    examples = {


        "大便": ("弟弟在廁所大便。", "dìdi zài cèsuǒ dàbiàn", "My younger brother is pooing in the toilet."),
        "星期天/星期日": ("星期天我們去公園。", "xīngqítiān wǒmen qù gōngyuán", "We go to the park on Sunday."),
        "圓/圓形": ("這個球是圓形的。", "zhège qiú shì yuánxíng de", "This ball is round."),

        "帽(子)": ("他戴著一頂紅色的帽子。", "tā dàizhe yī dǐng hóngsè de màozi", "He is wearing a red hat."),
        "裙(子)": ("妹妹穿著一條漂亮的裙子。", "mèimei chuānzhe yī tiáo piàoliang de qúnzi", "My younger sister is wearing a beautiful skirt."),
        "褲(子)": ("這條褲子太長了。", "zhè tiáo kùzi tài cháng le", "These pants are too long."),
        "鞋(子)": ("我的鞋子在哪裡？", "wǒ de xiézi zài nǎlǐ", "Where are my shoes?"),
        "襪(子)": ("他的襪子是白色的。", "tā de wàzi shì báisè de", "His socks are white."),

        "窗/窗戶": ("請把窗戶關上。", "qǐng bǎ chuānghu guān shàng", "Please close the window."),
        "櫃(子)": ("書在櫃子裡面。", "shū zài guìzi lǐmiàn", "The books are inside the cabinet."),
        "桌(子)": ("桌子上有一個蘋果。", "zhuōzi shàng yǒu yī gè píngguǒ", "There is an apple on the table."),
        "椅(子)": ("這張椅子很舒服。", "zhè zhāng yǐzi hěn shūfú", "This chair is very comfortable."),

        "刀(子)": ("請用刀子切水果。", "qǐng yòng dāozi qiē shuǐguǒ", "Please use a knife to cut the fruit."),
        "杯(子)": ("桌上有一個杯子。", "zhuō shàng yǒu yī gè bēizi", "There is a cup on the table."),
        "筷(子)": ("我會用筷子吃飯。", "wǒ huì yòng kuàizi chīfàn", "I can use chopsticks to eat."),

        "傘/雨傘": ("外面下雨了，記得帶雨傘。", "wàimiàn xiàyǔ le jìdé dài yǔsǎn", "It's raining outside, remember to bring an umbrella."),
        "照相機/照像機": ("這台照相機很貴。", "zhè tái zhàoxiàngjī hěn guì", "This camera is very expensive."),

        "開/打開": ("請幫我打開門。", "qǐng bāng wǒ dǎkāi mén", "Please help me open the door."),
        "照相/照像": ("我們在這裡照相吧。", "wǒmen zài zhèlǐ zhàoxiàng ba", "Let's take a picture here."),

        "(米)飯": ("我每天都吃米飯。", "wǒ měitiān dōu chī mǐfàn", "I eat rice every day."),
        "餃(子)": ("我最喜歡吃餃子。", "wǒ zuì xǐhuān chī jiǎozi", "I like eating dumplings the most."),

        "橘(子)": ("這個橘子很甜。", "zhège júzi hěn tián", "This tangerine is very sweet."),
        "番茄/蕃茄": ("番茄對身體很好。", "fānqié duì shēntǐ hěn hǎo", "Tomatoes are good for your health."),

        "橡皮/橡皮擦": ("我可以用你的橡皮擦嗎？", "wǒ kěyǐ yòng nǐ de xiàngpícā ma", "Can I use your eraser?")

        
            }

    for i in range(1, len(df)):
        raw_word = df.loc[i, "Unnamed: 2"]

        if pd.isna(raw_word):
            continue

        word = str(raw_word).strip()

        if word.startswith(("'", '"')) and word.endswith(("'", '"')):
            word = word[1:-1].strip()

        if word in examples:
            ex_chinese, ex_pinyin, ex_english = examples[word]

            df.loc[i, "Example"] = ex_chinese
            df.loc[i, "Example Pinyin"] = ex_pinyin
            df.loc[i, "Example Meaning"] = ex_english

    # overwrite the same Excel file
    df.to_excel(file_path, index=False)

    print("Finished! File updated.")


if __name__ == "__main__":
    main()