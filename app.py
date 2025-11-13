from flask import Flask, render_template

app = Flask(__name__)

SCENES = [
    {
        "title": "开场：月夜下的村庄",
        "description": "清冷的月光洒在幕布上，皮影人物缓缓登场。",
    },
    {
        "title": "英雄初现",
        "description": "少年英雄提灯而来，寻找失踪的神鸟。",
    },
    {
        "title": "龙影现身",
        "description": "传说中的龙影腾云驾雾，与少年相遇。",
    },
    {
        "title": "归于宁静",
        "description": "龙影归于天空，村庄重获安宁。",
    },
]


@app.route("/")
def index():
    return render_template("index.html", scenes=SCENES)


if __name__ == "__main__":
    app.run(debug=True)
