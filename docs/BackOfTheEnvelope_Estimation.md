# Back-of-the-envelope estimation

A rough estimate of how much data AdStream has to move every second and how much it has to store. It uses a few assumptions and simple arithmetic. It is not a measurement. We will replace the assumptions with real numbers once we can measure them.

**Units:** we use decimal units. 1 KB = 1,000 bytes, 1 MB = 1,000,000 bytes, 1 GB = 1,000 MB, 1 TB = 1,000 GB. Network speed is counted in bits, and 1 byte = 8 bits.

## The short version

| Question | Answer |
|---|---|
| Data arriving per second at the peak | 600 MB (4.8 Gbps) |
| Data arriving per second on average | 240 MB (1.92 Gbps) |
| Events per day | 34.56 billion |
| Raw data per day | 20.736 TB |
| Compressed data per day | 4.1472 TB |
| 30 days, raw | 622.08 TB |
| 30 days, compressed | 124.416 TB |

## 1. Assumptions

| What | Value | Where it comes from |
|---|---|---|
| Peak traffic | 1,000,000 events per second | Our design target. A goal for the design, not a measured speed |
| Average traffic | 400,000 events per second | Assumption. Over a whole day the traffic averages out lower than the peak |
| Size of one event | 600 bytes | Assumption. One event as JSON text, averaged over all event types |
| Compression | 5 to 1 | Assumption. Stored compressed, the data shrinks to one fifth of its size |

An **event** is one thing that happened, such as an ad being shown (an impression) or clicked. **JSON** is the text format an event arrives in. Some events are smaller and some are bigger, and 600 bytes is the average.

## 2. Throughput: how much data arrives each second

Throughput means how many bytes arrive every second.

**Step 1. Bytes per second at the peak.**

1,000,000 events per second × 600 bytes per event = 600,000,000 bytes per second

600,000,000 bytes is 600 MB, so the peak is **600 MB per second**.

**Step 2. Convert to network speed.** Networks are measured in bits, and 1 byte is 8 bits.

600 MB per second × 8 = 4,800 megabits per second = **4.8 Gbps** (gigabits per second)

In plain words: at the peak, our event data alone would fill about half of a 10 Gbps network link.

**Step 3. The same for the average.**

400,000 events per second × 600 bytes = 240,000,000 bytes per second = **240 MB per second**

240 MB per second × 8 = **1.92 Gbps**

| | Events per second | Data per second | Network speed |
|---|---|---|---|
| Peak | 1,000,000 | 600 MB | 4.8 Gbps |
| Average | 400,000 | 240 MB | 1.92 Gbps |

The peak is 2.5 times the average (1,000,000 ÷ 400,000).

These figures count only the event data itself. Real network traffic is a bit higher because of headers and protocols. We leave that out for now.

## 3. Storage: how much data piles up

Storage depends on the **average** rate, not the peak, because the peak only lasts a short part of the day.

**Step 1. Events per day.** A day has 86,400 seconds (24 × 60 × 60).

400,000 events per second × 86,400 seconds = 34,560,000,000 events, which is **34.56 billion events per day**

**Step 2. Raw size per day** (JSON text, not compressed).

34,560,000,000 events × 600 bytes = 20,736,000,000,000 bytes = **20.736 TB per day**

Check: 240 MB per second × 86,400 seconds gives the same 20.736 TB.

**Step 3. Compressed size per day** (5 to 1).

20.736 TB ÷ 5 = **4.1472 TB per day**, about 4.15 TB

**Step 4. 30 days.**

| | Per day | 30 days |
|---|---|---|
| Raw | 20.736 TB | 622.08 TB |
| Compressed (5 to 1) | 4.1472 TB | 124.416 TB (about 124.4 TB) |

In plain words: at the raw rate, a 1 TB drive would fill up in about 69 minutes. Compression is what keeps a month of data near 124 TB instead of 622 TB.

This is the size of **one copy** of the data.

Most of these need measured numbers, such as the real event size, the real compression ratio and the real speed of one machine. We add them when we can measure.
