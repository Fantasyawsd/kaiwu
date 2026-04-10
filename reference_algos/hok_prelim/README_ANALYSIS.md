# 初赛
初赛代码也升级到了v2，进行了一些包装的优化，调用逻辑也和去年有少许不同

## PPO代码结构分析
> 下文都按照`remote`逻辑（分布式）进行分析

还是和去年逻辑图类似：
![逻辑图]()

- learner: 实例化一个[agent.py](./code/agent_ppo/agent.py)中的`Agent`用于模型训练`agent.learn`，保存模型，更新`model_pool`，图中相关功能包含：
    - 采样策略自动从buffer中采样得到`NumpyData2SampleData`传入到`agent.learn`中，采样频率为`learner_train_sleep_seconds`，更新模型
    - 根据`dump_model_freq`自动存储模型到`model_pool`中
    - aisrv通过`train_workflow.py`中`agent.save_model()`让learner保存模型到本地
    - aisrv通过`train_workflow.py`中`agent.load_model(id="lastest")`从`model_pool`中拉取最新的模型
- actor: 实例化一个`Agent`（当且仅当：`predict_local_or_remote`为`remote`使用actor预测，否则`aisrv`在本地进行预测）用于模型预测`agent.predict`和`load_model`
    - `load_model`由`aisrv`通过`train_workflow.py`控制频率
    - `agent.predict`通过`aisrv`调用`agent.predict`进行预测
- aisrv：

aisrv下拉actor的模型，并和自己的环境进行交互，代码为[`train_workflow.py`](./code/agent_ppo/workflow/train_workflow.py)

通过`NumpyData2SampleData`对buffer按照[`configure_app.toml`](hok_prelim/code/conf/configure_app.toml)采样得到`SampleData`

## 一点疑问
1. [`configure_app.toml`](./code/conf/configure_app.toml)中的`learner_train_by_while_true`和`learner_train_sleep_seconds`，`production_consume_ratio`这二者到底是使用那一种采样策略，需要查看下源码
