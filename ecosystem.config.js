module.exports = {
  apps : [{
    name   : "LLM4Table",
    script : "./main.py",
    interpreter: "python3",
    env: {
      "PORT": "8000",
      "HOST": "0.0.0.0"
    }
  }]
}