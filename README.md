# Master's thesis: LLM4DD

> Autonomous driving systems (ADSs) should be capable of tackling any challenge
> they may be faced with while driving. Before deploying such ADSs, it is
> important to be confident that they are capable of handling potential
> challenges in a fitting manner. But there is a near infinite set of potential
> scenarios that an ADS may be faced with, making it impossible to predict and
> test on all possible scenarios in advance. To this end, we propose using Large
> Language Models (LLMs) to decrease the driveability of our existing ADS
> scenarios, enabling the ADS to face a more challenging test environment. By
> using these more challenging test scenarios, we can either (1) cause it to
> fail and analyse why the ADS failed, or (2) increase our confidence in it
> being able to operate in challenging scenarios. We implement a tool — LLM4DD —
> for doing this and evaluate it with regard to the jerk metric. We compare the
> jerk of the ADS in the ‘base’ and ‘enhanced’ versions of the scenario,
> assessing if the driveability was decreased and how the ADS responded to this
> more challenging operating environment. We also perform a literature review to
> survey the relevant related works and evaluate how LLM4DD fits into the state
> of the art. Experimental results indicate that using LLMs to decrease
> driveability is a promising strategy if the range of the changes the LLM is
> allowed to make is limited, whereas problems related to hallucination and
> simulator crashes arise if the LLM makes excessive changes to the original
> scenario. Based on the results, we present the research and outline several
> strategies for improving LLM4DD in future research.

Compiled PDF of the thesis [is available here](https://orjahren.github.io/master/thesis.pdf).

Code for the tool and thesis experiments is located in [this standalone
repo](https://github.com/orjahren/LLM4MDD). This repo contains the LaTeX source
files.

The thesis was written at [Simula Research Laboratory](https://simula.no).
<br/><br/>The thesis currently has 112 / 100 pages, which is
112.00 percent.
