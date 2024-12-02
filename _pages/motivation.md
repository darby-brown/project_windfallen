---
permalink: /Motivation/
title: "Motivation"
---

## Approximately 38% of all food is wasted in the US. 

A substantial amount of this waste happens at the farm level. A study by Santa Clara University found that field losses of edible produce are approximately 33.7% of marketed yield. Windfallen team is building technology to reduce US food waste.

Advancements in robotic technology are primed to overhaul the agriculture industry, where ~30-40% of farm operating costs are currently spent on seasonal labor. Employing seasonal labor to harvest produce poses numerous challenges–one such problem is that of windfallen fruit. On a ripe apple tree, a fall breeze or a hot day can cause large numbers of fruit to fall from the branches. In the past, these ‘windfallen’ fruit were collected and used for processed foodstuffs like cider. Nowadays, more and more apples are left to rot on the ground because increasing labor costs do not justify their collection.

## The collection of windfallen apples, and by extension other windfallen fruit, is a promising area for robotic deployment. 

We expect this solution to reduce food waste while not threatening workers’ livelihood. We propose deployment of a multi-agent fleet composed of “picker” bots and “bin” bots that collaborate to collect windfallen apples.

However, successful robotic deployment is a notoriously difficult task, especially in natural environments such as apple orchards. Such robots are expected to have a number of capabilities, including:

- Ability to collaborate to maximize fruit collected and minimize time to collect.
- Ability to pick up a windfallen apple, turn it over, and gauge “pickability”. Rotten apples should not be picked. 
- Ability to navigate uneven and inconsistent terrain.

At the early stages of development, the Windfallen team is focused on the **ability to collaborate** across a multi-robot fleet. 

## Can robots work together?

A critical innovation in the field of robotics is that of robotic collaboration. In other words, how do you get robots to collaborate with each other toward a common goal? Multiple startups focus solely on this task, and the burgeoning field of multi-agent reinforcement learning (MARL) offers a promising machine-learning based approach. As the field of robotics approaches its “GPT moment”, as predicted by Y Combinator, the demand for MARL technology in real-world contexts is likely to grow.

Research in this field has largely been conducted in simple, 2D environments that minimally represent real-world circumstances. InstaDeep’s Jumanji, for example, offers 22 such environments. Our research aims to push MARL toward more real-world scenarios by providing a novel environment that is representative of the variability seen on an actual apple orchard. In conducting this research, we achieve the first step for deployment of the robotic fleet envisioned above and provide valuable insight for the MARL community on the viability of MARL in real world settings. 