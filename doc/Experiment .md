Optimization Parameters:

NaCl 		10–35 g/L    
Glucose 	1–20 g/L  
Yeast extract 	2–10 g/L 

pH osmalirity 

***Input:***	initial recipe  
(10 g/L Tryptone; 5 g/L Yeast Extract ; 10 g/L NaCl; 0 g/L Glucose ) 

***AI agent:***		possible conditions in g/L 

***Compiler:***		g/L recalculated in uL to prepare 1mL of media stock solution

***Experiment:***		robot mixes media stock solutions and add to the cells

***Incubation:*** 		plates with cells incubated 2-4 hours in 37C

***OD Measurement:*** 	plate with cells goes into plate reader to read OD at 600

***Parser:***	OD recalculated in growth rate that would be transferred back  in AI agent

***AI agent gives new conditions and loop repeats***

Benchmark is growth rate in media with initial recipe

Stock solutions:

Tryptone (vegetable) 		100 mg/mL  
Yeast extract 			100 mg/mL  
Sodium Chloride (NaCl) 	5 M (292.2 mg/mL)  
Glucose 			100 mg/mL  
MOPS(ph adjusted to 7\) 	1M

Initial Recipe: 

10 g/L		Tryptone  
5 g/L		Yeast Extract   
10 g/L		NaCl  
0 g/L		Glucose 

Important Notes:

1. Avoid edge effect \- fill outer wells with water or buffer \- we can use only 60 wells per plate  
2. Glucose and salt creates particles with time that could be mistaken with cells when reading OD600 \- we would need blank wells without cells to substruct   
     
     
   

60 wells   
replicates of 3wells \+ 1 well as a blank \= 4 wells per optimization point   
60/4=15

We need standard media as control, so we can test 14 conditions per plate

For 4 wells we need 200 uL x 4= 800 uL   
Lets create 1mL of each media type 

For 1mL of media we would use:

100 mL of 100 mg/mL Tryptone (10 mg/mL / 100 mg/mL \* 3000mL	)  
50 mL of  100 mg/mLYeast Extract   
34.2 mL of 5 M NaCl  
815.8 mL of MOPS(ph adjusted to 7\)