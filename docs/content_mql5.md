# Ichimoku & ADX-Wilder Trading Strategy Guide

> **Source:** [MQL5 Article](https://www.mql5.com/en/articles/18723)

## 📋 Introduction

The **Ichimoku Kinko Hyo (Ichimoku)** indicator and **ADX-Wilder (ADX)** oscillator are used in this article in a support/resistance and trend-identification pairing. The Ichimoku is certainly multifaceted and quite versatile. It can provide more than just support/resistance levels. However, we are sticking to just S/R for now. 

**Indicator pairings**, especially when complimentary, have the potential to spawn more incisive and accurate entry signals for Expert Advisors. As usual, we examine **10 signal patterns** of this indicator pairing. We test these 10 signal patterns that are each assigned an index, one at a time, while being guided by these rules:

### 🔢 Pattern Indexing System

**Indexing is from 0 to 9** allowing us to easily compute the map value for their exclusive use by the Expert Advisor:

- If a pattern is indexed **1**, set parameter `PatternsUsed` to 2¹ = **2**
- If a pattern is indexed **4**, set parameter `PatternsUsed` to 2⁴ = **16**  
- **Maximum value**: 1023 (since we have only 10 parameters)
- Any number between 0 and 1023 that is not a pure exponent of 2 represents a **combination** of more than one pattern

### ⚠️ Important Testing Philosophy

In previous articles we have argued why training or optimizing with **multiple signals** is bound to be futile despite the rosy test results they often present. This is because when more than one signal is engaged, they tend to inadvertently cancel each other's trades at points that are convenient for maximizing profits in that limited test window. Tests could be made on wider test windows in order to work around this, but since this article is focused on a **one-year test window**, that would not be applicable for our purposes.

---

## 🌸 The Ichimoku Indicator

By definition, the **Ichimoku** is a comprehensive indicator that brings together several elements to assess trend direction, momentum and S/R. An indicator whose name translates to **"all-in-one system"**, it seeks to give a holistic view of price action and is often used for trend following strategies.

### 📊 Five Key Components

The Ichimoku constitutes **five buffers**:
1. **Tenkan-sen** (Conversion Line)
2. **Kijun-sen** (Base Line)  
3. **Senkou-Span-A** (Leading Span A)
4. **Senkou-Span-B** (Leading Span B)
5. **Chikou-Span** (Lagging Span)

In addition to these buffers, a **Kumo-Cloud** is also often referred to, being constituted of the two Senkou-Spans A and B. Prima facie, this cloud can serve as an S/R marker and also a metric of trend strength depending on its thickness.

### ⚙️ Default Parameters

The inputs required to calculate all five buffers are three, and they are typically assigned:
- **9** periods
- **26** periods  
- **52** periods

> **💡 Pro Tip:** On paper, these values can be customized for various markets, but one is probably better off leaving these periods as is and looking to adjust other attributes of the system.

### 📐 Mathematical Formulas

#### 1. **Tenkan-sen (9-period)**
```
Tenkan-sen = (Highest High + Lowest Low) / 2
```
**Where:**
- Highest High = maximum price over the last **9** periods
- Lowest Low = minimum price over the last **9** periods
- **Purpose:** Short-term trend indicator sensitive to price changes

#### 2. **Kijun-sen (26-period)**
```
Kijun-sen = (Highest High + Lowest Low) / 2
```
**Where:**
- Highest High = maximum price over **26** periods
- Lowest Low = minimum price over **26** periods
- **Purpose:** Medium-term trend barometer that can also serve as S/R

#### 3. **Senkou Span A**
```
Senkou Span A = (Tenkan-sen + Kijun-sen) / 2
```
**Where:**
- Values are plotted **26 periods ahead**
- **Purpose:** Forms one edge of the Kumo cloud for S/R analysis

#### 4. **Senkou Span B (52-period)**
```
Senkou Span B = (Highest High + Lowest Low) / 2
```
**Where:**
- Highest High = maximum price over **52** periods
- Lowest Low = minimum price over **52** periods
- Values are plotted **26 periods ahead**
- **Purpose:** Forms the second edge of the Kumo cloud; long-term S/R

#### 5. **Chikou Span**
```
Chikou Span = Current period's close
```
**Where:**
- Close price is plotted **26 periods back**
- **Purpose:** Confirms trends by comparing past price to current action

### 🌥️ Kumo Cloud Analysis

The **Kumo cloud** is the area between Senkou Span A and Senkou Span B:
- **Bullish Cloud:** When Span A > Span B 
- **Bearish Cloud:** When Span A < Span B
- **Function:** Visualizes trend strength and S/R levels

---

## 📈 The ADX-Wilder Indicator

Our second indicator measures the **strength** of a prevalent trend - **not its direction**. It features 2 additional buffers, besides its primary, that can be used to assess bullish and bearish momentum.

### 🎯 Key Characteristics

- **Range:** 0 to 100 (seldom breaches 25)
- **Strong Trend:** ADX ≥ 25
- **Weak Trend:** ADX < 20
- **Type:** Lagging indicator
- **Default Period:** 14

### 📊 Buffer Components

The ADX Wilder outputs **3 buffers** but works with up to **6 different buffers** in the process:

1. **+DM** (Positive Directional Movement)
2. **+DI** (Positive Directional Indicator)
3. **-DM** (Negative Directional Movement)
4. **-DI** (Negative Directional Indicator)
5. **True Range**
6. **ADX** (Main buffer)

### 📐 Mathematical Formulas

#### 1. **Positive Directional Movement (+DM)**
```
+DM = Current High - Previous High
```
**Condition:** Previous Low > Current Low, otherwise +DM = 0
**Purpose:** Tracks upward price movement

#### 2. **Negative Directional Movement (-DM)**
```
-DM = Previous Low - Current Low
```
**Condition:** Current High > Previous High, otherwise -DM = 0
**Purpose:** Measures downward price movement

#### 3. **True Range (TR)**
```
TR = Max[(Current High - Current Low), 
         |Current High - Previous Close|, 
         |Current Low - Previous Close|]
```
**Purpose:** Measures price volatility

#### 4. **Positive Directional Indicator (+DI)**
```
+DI = (Smoothed +DM / Smoothed TR) × 100
```
**Purpose:** Indicates bullish strength

#### 5. **Negative Directional Indicator (-DI)**
```
-DI = (Smoothed -DM / Smoothed TR) × 100
```
**Purpose:** Measures bearish strength

#### 6. **ADX Main Buffer**
```
ADX = Smoothed[(|+DI - -DI| / (+DI + -DI)) × 100]
```
**Where:**
- Smoothing = exponential averaging over 14 periods
- Non-smoothed value = DX
- **Purpose:** Quantifies trend strength

### 📋 Testing Parameters

**All testing parameters:**
- **Test Period:** 2023 (with 2024 as walk-forward)
- **Timeframe:** 30-minute (instead of regular 4-hour due to signal frequency)
- **Symbol:** GBP/USD

---

## 🎯 Trading Patterns (0-9)

### 📊 Pattern 0: Price Crossing Senkou Span A with ADX Confirmation

**🟢 Bullish Signal:**
- Price crosses **above** Senkou Span A (breakout above Kumo cloud)
- ADX ≥ **25**

**🔴 Bearish Signal:**
- Price crosses **below** Senkou Span A (breakdown below cloud)
- ADX ≥ **25**

```cpp
//+------------------------------------------------------------------+
//| Check for Pattern 0.                                             |
//+------------------------------------------------------------------+
bool CSignalIchimoku_ADXWilder::IsPattern_0(ENUM_POSITION_TYPE T)
{  
   if(T == POSITION_TYPE_BUY && 
      Close(X() + 1) < Ichimoku_SenkouSpanA(X() + 1) && 
      Close(X()) > Ichimoku_SenkouSpanA(X()) && 
      ADX(X()) >= 25.0)
   {  return(true); }
   
   else if(T == POSITION_TYPE_SELL && 
      Close(X() + 1) > Ichimoku_SenkouSpanA(X() + 1) && 
      Close(X()) < Ichimoku_SenkouSpanA(X()) && 
      ADX(X()) >= 25.0)
   {  return(true); }
   
   return(false);
}
```

**📈 Test Results:** r0

**✅ Best Practices:**
- Confirm on higher timeframes for trend alignment
- ADX ≥ 25 is essential for filtering weak signals
- Set stop-loss below/above Kumo cloud
- Monitor for false breakouts
- **Best Context:** Trending markets (avoid choppy conditions)

---

### 📊 Pattern 1: Tenkan-Sen/Kijun-Sen Crossover with ADX Confirmation

**🟢 Bullish Signal:**
- Tenkan-Sen crosses **above** Kijun-Sen
- ADX ≥ **20**

**🔴 Bearish Signal:**
- Tenkan-Sen crosses **below** Kijun-Sen  
- ADX ≥ **20**

```cpp
//+------------------------------------------------------------------+
//| Check for Pattern 1.                                             |
//+------------------------------------------------------------------+
bool CSignalIchimoku_ADXWilder::IsPattern_1(ENUM_POSITION_TYPE T)
{  
   if(T == POSITION_TYPE_BUY && 
      Ichimoku_TenkanSen(X() + 1) < Ichimoku_KijunSen(X() + 1) && 
      Ichimoku_TenkanSen(X()) > Ichimoku_KijunSen(X()) && 
      ADX(X()) >= 20.0)
   {  return(true); }
   
   else if(T == POSITION_TYPE_SELL && 
      Ichimoku_TenkanSen(X() + 1) > Ichimoku_KijunSen(X() + 1) && 
      Ichimoku_TenkanSen(X()) < Ichimoku_KijunSen(X()) && 
      ADX(X()) >= 20.0)
   {  return(true); }
   
   return(false);
}
```

**📈 Test Results:** r1

**⚠️ Performance:** Struggled to forward walk
**✅ Improvements:**
- Use in direction of higher timeframe trend
- Set stop-loss below/above Kijun-Sen
- Combine with volume indicators
- **Best Context:** Trend genesis or fractal points

---

### 📊 Pattern 2: Senkou Span A/B Crossover with ADX Confirmation

**🟢 Bullish Signal:**
- Senkou Span A crosses **above** Senkou Span B (bullish cloud formation)
- ADX ≥ **25**

**🔴 Bearish Signal:**
- Senkou Span A crosses **below** Senkou Span B (bearish cloud formation)
- ADX ≥ **25**

```cpp
//+------------------------------------------------------------------+
//| Check for Pattern 2.                                             |
//+------------------------------------------------------------------+
bool CSignalIchimoku_ADXWilder::IsPattern_2(ENUM_POSITION_TYPE T)
{  
   if(T == POSITION_TYPE_BUY && 
      Ichimoku_SenkouSpanA(X() + 1) < Ichimoku_SenkouSpanB(X() + 1) && 
      Ichimoku_SenkouSpanA(X()) > Ichimoku_SenkouSpanB(X()) && 
      ADX(X()) >= 25.0)
   {  return(true); }
   
   else if(T == POSITION_TYPE_SELL && 
      Ichimoku_SenkouSpanA(X() + 1) > Ichimoku_SenkouSpanB(X() + 1) && 
      Ichimoku_SenkouSpanA(X()) < Ichimoku_SenkouSpanB(X()) && 
      ADX(X()) >= 25.0)
   {  return(true); }
   
   return(false);
}
```

**📈 Test Results:** r2

**✅ Performance:** Forward walks well
**✅ Best Practices:**
- Confirm cloud crossover on higher timeframes
- ADX 25 threshold is key
- Avoid when cloud is thin
- **Best Context:** Trending markets for swing trading

---

### 📊 Pattern 3: Price Bounce/Rejection at Cloud with ADX and DI Confirmation

**🟢 Bullish Signal:**
- Price bounces off top of Kumo (Senkou-Span-A)
- ADX ≥ **25**
- +DI > -DI

**🔴 Bearish Signal:**
- Price rejects cloud bottom (Senkou-Span-A) in U formation
- ADX ≥ **25**
- -DI > +DI

```cpp
//+------------------------------------------------------------------+
//| Check for Pattern 3.                                             |
//+------------------------------------------------------------------+
bool CSignalIchimoku_ADXWilder::IsPattern_3(ENUM_POSITION_TYPE T)
{  
   if(T == POSITION_TYPE_BUY && 
      Close(X() + 2) > Close(X() + 1) && Close(X() + 1) < Close(X()) &&
      Close(X() + 2) > Ichimoku_SenkouSpanA(X() + 2) && 
      Close(X()) > Ichimoku_SenkouSpanA(X()) && 
      Close(X() + 1) <= Ichimoku_SenkouSpanA(X() + 1) && 
      ADX_Plus(X()) > ADX_Minus(X()) && ADX(X()) >= 25.0)
   {  return(true); }
   
   else if(T == POSITION_TYPE_SELL &&  
      Close(X() + 2) < Close(X() + 1) && Close(X() + 1) > Close(X()) &&
      Close(X() + 2) < Ichimoku_SenkouSpanA(X() + 2) && 
      Close(X()) < Ichimoku_SenkouSpanA(X()) && 
      Close(X() + 1) >= Ichimoku_SenkouSpanA(X() + 1) && 
      ADX_Plus(X()) < ADX_Minus(X()) && ADX(X()) >= 25.0)
   {  return(true); }
   
   return(false);
}
```

**📈 Test Results:** r3

**✅ Performance:** Positive forward walk
**✅ Best Practices:**
- Confirm with candlestick patterns (pin bars)
- Ensure DI alignment matches price trend
- Set stop-loss below/above Senkou-Span-B
- **Best Context:** Range-to-trend transitions

---

### 📊 Pattern 4: Chikou Span vs. Senkou Span A with ADX Confirmation

**🟢 Bullish Signal:**
- Chikou Span > Senkou Span A
- ADX ≥ **25**

**🔴 Bearish Signal:**
- Chikou Span < Senkou Span A
- ADX ≥ **25**

```cpp
//+------------------------------------------------------------------+
//| Check for Pattern 4.                                             |
//+------------------------------------------------------------------+
bool CSignalIchimoku_ADXWilder::IsPattern_4(ENUM_POSITION_TYPE T)
{  
   if(T == POSITION_TYPE_BUY && 
      Ichimoku_ChinkouSpan(X() + 26) > Ichimoku_SenkouSpanA(X()) &&  
      ADX(X()) >= 25.0)
   {  return(true); }
   
   else if(T == POSITION_TYPE_SELL &&  
      Ichimoku_ChinkouSpan(X() + 26) < Ichimoku_SenkouSpanA(X()) &&  
      ADX(X()) >= 25.0)
   {  return(true); }
   
   return(false);
}
```

**📈 Test Results:** r4

**✅ Performance:** Forward walks very well
**💡 Note:** 26-period manual shift required for Chikou buffer
**✅ Best Practices:**
- Better for trend confirmation than entry signals
- Pair with other Ichimoku signals
- Set stop-loss based on recent swing points
- **Best Context:** Trending markets only

---

### 📊 Pattern 5: Price Bounce/Rejection at Tenkan-Sen with ADX and DI Confirmation

**🟢 Bullish Signal:**
- Price bounces off Tenkan-Sen
- ADX ≥ **25**
- +DI > -DI

**🔴 Bearish Signal:**
- Price rejects Tenkan-Sen as resistance
- ADX ≥ **25** 
- -DI > +DI

```cpp
//+------------------------------------------------------------------+
//| Check for Pattern 5.                                             |
//+------------------------------------------------------------------+
bool CSignalIchimoku_ADXWilder::IsPattern_5(ENUM_POSITION_TYPE T)
{  
   if(T == POSITION_TYPE_BUY && 
      Close(X() + 2) > Close(X() + 1) && Close(X() + 1) < Close(X()) &&
      Close(X() + 2) > Ichimoku_TenkanSen(X() + 2) && 
      Close(X()) > Ichimoku_TenkanSen(X()) && 
      Close(X() + 1) <= Ichimoku_TenkanSen(X() + 1) && 
      ADX_Plus(X()) > ADX_Minus(X()) && ADX(X()) >= 25.0)
   {  return(true); }
   
   else if(T == POSITION_TYPE_SELL &&  
      Close(X() + 2) < Close(X() + 1) && Close(X() + 1) > Close(X()) &&
      Close(X() + 2) < Ichimoku_TenkanSen(X() + 2) && 
      Close(X()) < Ichimoku_TenkanSen(X()) && 
      Close(X() + 1) >= Ichimoku_TenkanSen(X() + 1) && 
      ADX_Plus(X()) < ADX_Minus(X()) && ADX(X()) >= 25.0)
   {  return(true); }
   
   return(false);
}
```

**📈 Test Results:** r5

**❌ Performance:** Completely fails to forward walk
**✅ Potential Improvements:**
- Add candlestick confirmation
- Include DI threshold checks
- Implement stop-loss below/above Tenkan-Sen
- **Best Context:** Trending markets with pullbacks

---

### 📊 Pattern 6: Price Crossing Kijun-Sen with ADX and DI Confirmation

**🟢 Bullish Signal:**
- Price crosses Kijun-Sen from below to above
- +DI > -DI
- ADX ≥ **25**

**🔴 Bearish Signal:**
- Price crosses Kijun-Sen from above to below
- -DI > +DI
- ADX ≥ **25**

```cpp
//+------------------------------------------------------------------+
//| Check for Pattern 6.                                             |
//+------------------------------------------------------------------+
bool CSignalIchimoku_ADXWilder::IsPattern_6(ENUM_POSITION_TYPE T)
{  
   if(T == POSITION_TYPE_BUY && 
      Close(X() + 1) < Ichimoku_KijunSen(X() + 1) && 
      Close(X()) > Ichimoku_KijunSen(X()) && 
      ADX_Plus(X()) > ADX_Minus(X()) && ADX(X()) >= 25.0)
   {  return(true); }
   
   else if(T == POSITION_TYPE_SELL && 
      Close(X() + 1) > Ichimoku_KijunSen(X() + 1) && 
      Close(X()) < Ichimoku_KijunSen(X()) && 
      ADX_Plus(X()) < ADX_Minus(X()) && ADX(X()) >= 25.0)
   {  return(true); }
   
   return(false);
}
```

**📈 Test Results:** r6

**⚠️ Performance:** Struggles to forward walk
**✅ Improvements:**
- Consider higher timeframe cloud directions
- Implement stop-loss below/above Kijun-Sen
- **Best Context:** Established trending environments

---

### 📊 Pattern 7: Price Bounce/Rejection at Senkou Span B with ADX Confirmation

**🟢 Bullish Signal:**
- Price bounces off Senkou Span B (acting as support)
- Span A > Span B (within Kumo cloud)
- ADX ≥ **20**

**🔴 Bearish Signal:**
- Price rejects Span B as resistance
- Span B > Span A (within Kumo cloud)
- ADX ≥ **20**

```cpp
//+------------------------------------------------------------------+
//| Check for Pattern 7.                                             |
//+------------------------------------------------------------------+
bool CSignalIchimoku_ADXWilder::IsPattern_7(ENUM_POSITION_TYPE T)
{  
   if(T == POSITION_TYPE_BUY && 
      Close(X() + 2) > Close(X() + 1) && Close(X() + 1) < Close(X()) &&
      Close(X() + 2) > Ichimoku_SenkouSpanB(X() + 2) && 
      Close(X()) > Ichimoku_SenkouSpanB(X()) && 
      Close(X() + 1) <= Ichimoku_SenkouSpanB(X() + 1) && 
      Ichimoku_SenkouSpanA(X()) > Ichimoku_SenkouSpanB(X()) && 
      ADX(X()) >= 20.0)
   {  return(true); }
   
   else if(T == POSITION_TYPE_SELL &&  
      Close(X() + 2) < Close(X() + 1) && Close(X() + 1) > Close(X()) &&
      Close(X() + 2) < Ichimoku_SenkouSpanB(X() + 2) && 
      Close(X()) < Ichimoku_SenkouSpanB(X()) && 
      Close(X() + 1) >= Ichimoku_SenkouSpanB(X() + 1) && 
      Ichimoku_SenkouSpanA(X()) < Ichimoku_SenkouSpanB(X()) && 
      ADX(X()) >= 20.0)
   {  return(true); }
   
   return(false);
}
```

**📈 Test Results:** r7

**✅ Performance:** Able to forward walk
**✅ Best Practices:**
- Add candlestick pattern confirmation
- Tight stop-loss below/above Span B
- Avoid with thin clouds or low ADX
- **Best Context:** Deep pullbacks in trends

---

### 📊 Pattern 8: Price Above/Below Cloud with ADX Confirmation

**🟢 Bullish Signal:**
- Price above Kumo cloud
- Span A > Span B
- ADX ≥ **25**

**🔴 Bearish Signal:**
- Price below Kumo cloud  
- Span B > Span A
- ADX ≥ **25**

```cpp
//+------------------------------------------------------------------+
//| Check for Pattern 8.                                             |
//+------------------------------------------------------------------+
bool CSignalIchimoku_ADXWilder::IsPattern_8(ENUM_POSITION_TYPE T)
{  
   if(T == POSITION_TYPE_BUY && 
      Close(X() + 1) < Close(X()) &&
      Close(X() + 1) > Ichimoku_SenkouSpanA(X() + 1) && 
      Close(X()) > Ichimoku_SenkouSpanA(X()) && 
      Ichimoku_SenkouSpanA(X()) > Ichimoku_SenkouSpanB(X()) && 
      ADX(X()) >= 25.0)
   {  return(true); }
   
   else if(T == POSITION_TYPE_SELL &&  
      Close(X() + 1) > Close(X()) &&
      Close(X() + 1) < Ichimoku_SenkouSpanA(X() + 1) && 
      Close(X()) < Ichimoku_SenkouSpanA(X()) && 
      Ichimoku_SenkouSpanA(X()) > Ichimoku_SenkouSpanB(X()) && 
      ADX(X()) >= 25.0)
   {  return(true); }
   
   return(false);
}
```

**📈 Test Results:** r8

**🏆 Performance:** **BEST PERFORMER** - Forward walk results surpass test results
**✅ Best Practices:**
- Consider price trend direction before entry
- Set stop-loss at comfortable distance below/above cloud
- **Best Context:** Trend continuation setups

---

### 📊 Pattern 9: Chikou Span vs. Price and Cloud with ADX Confirmation

**🟢 Bullish Signal:**
- Chikou Span > Senkou Span A
- Span A > Span B
- ADX ≥ **25**

**🔴 Bearish Signal:**
- Chikou Span < Senkou Span A
- Span A < Span B  
- ADX ≥ **25**

```cpp
//+------------------------------------------------------------------+
//| Check for Pattern 9.                                             |
//+------------------------------------------------------------------+
bool CSignalIchimoku_ADXWilder::IsPattern_9(ENUM_POSITION_TYPE T)
{  
   if(T == POSITION_TYPE_BUY && 
      Ichimoku_ChinkouSpan(X() + 26) > Ichimoku_SenkouSpanA(X()) &&
      Ichimoku_SenkouSpanA(X()) > Ichimoku_SenkouSpanB(X()) && 
      ADX(X()) >= 25.0)
   {  return(true); }
   
   else if(T == POSITION_TYPE_SELL &&  
      Ichimoku_ChinkouSpan(X() + 26) < Ichimoku_SenkouSpanA(X()) &&
      Ichimoku_SenkouSpanA(X()) < Ichimoku_SenkouSpanB(X()) && 
      ADX(X()) >= 25.0)
   {  return(true); }
   
   return(false);
}
```

**📈 Test Results:** r9

**⚠️ Performance:** Eventually profitable but struggles compared to Pattern 8 and 4
**✅ Improvements:**
- Add secondary confirmation with other Ichimoku patterns
- Ensure cloud supports trade direction
- Set stop-loss based on recent price action
- **Best Context:** Strongly trending markets only

---

## 📊 Performance Summary

| Pattern | Description | Performance | ADX Threshold | Best Context |
|---------|-------------|-------------|---------------|--------------|
| **0** | Price × Senkou Span A | ✅ Forward walks | ≥25 | Trending markets |
| **1** | Tenkan × Kijun | ❌ Struggled | ≥20 | Trend genesis |
| **2** | Span A × Span B | ✅ Forward walks | ≥25 | Swing trading |
| **3** | Cloud Bounce/Reject | ✅ Positive | ≥25 | Range-to-trend |
| **4** | Chikou × Span A | ✅ Very good | ≥25 | Trending markets |
| **5** | Tenkan Bounce/Reject | ❌ Failed | ≥25 | Trending pullbacks |
| **6** | Price × Kijun | ⚠️ Struggled | ≥25 | Established trends |
| **7** | Span B Bounce/Reject | ✅ Forward walks | ≥20 | Deep pullbacks |
| **8** | Price vs Cloud | 🏆 **BEST** | ≥25 | Trend continuation |
| **9** | Chikou × Price & Cloud | ⚠️ Struggled | ≥25 | Strong trends |

---

## 🎯 Conclusion

We have introduced another indicator pairing of the **Ichimoku indicator** and the **ADX Wilder**. This pairing, based on the limited 2-year time window of testing, has given us potentially **seven signal patterns** that could forward walk profitably:

### ✅ **Successful Patterns:**
- **Pattern 0:** Price Crossing Senkou Span A
- **Pattern 2:** Senkou Span A/B Crossover  
- **Pattern 3:** Price Bounce/Rejection at Cloud
- **Pattern 4:** Chikou Span vs. Senkou Span A
- **Pattern 7:** Price Bounce/Rejection at Senkou Span B
- **Pattern 8:** Price Above/Below Cloud (**Best Performer**)

### ❌ **Struggled Patterns:**
- **Pattern 1:** Tenkan-Sen/Kijun-Sen Crossover
- **Pattern 5:** Price Bounce/Rejection at Tenkan-Sen  
- **Pattern 6:** Price Crossing Kijun-Sen

> **⚠️ Disclaimer:** We are speaking potentially here because the test window we are using is very small, and as always the gist of this article is to be exploratory. 

**🔮 Next Steps:** In the next piece we will try to examine the three signal patterns that struggled to forward walk and see if machine learning can play a role, if at all, in turning their fortunes around.
