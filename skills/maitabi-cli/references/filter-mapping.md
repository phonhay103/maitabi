# Maitabi Bus Filter Mapping Reference

This document provides a comprehensive mapping reference between UI Labels and internal ID query values used in Maitabi URLs (`bus.maitabi.jp` & `api.bus.maitabi.jp`).

---

## 1. Point of Departure (`departure` / 発着地)

| Query ID | Japanese Label | English Description |
| :---: | :--- | :--- |
| `1` | 東京 | Departure from Tokyo (Takebashi / Shinjuku) |
| `2` | 大阪・京都 | Departure from Osaka / Kyoto |
| `3` | 名古屋 | Departure from Nagoya |

---

## 2. Area / Direction (`area` / 方面)

Query parameter: `area={id}`

| Query ID | Area Name (Japanese) |
| :---: | :--- |
| `0` | All / Select area (全方面) |
| `1` | 恵那山 (Mt. Ena) |
| `2` | 芝沢ゲート (Shibasawa Gate) |
| `3` | 塩見（鳥倉） (Shiomi / Torikura) |
| `4` | 木曽駒（菅の台）/仙丈・甲斐駒（戸台口） (Kisokoma / Senjo / Kaikoma) |
| `5` | 御嶽山（ロープウェイ駅） (Mt. Ontake Ropeway) |
| `6` | 畑薙・荒川・赤石・聖・光 (Hatanagi / Arakawa / Akaishi / Hijiri / Tekari) |
| `10` | 上高地 (Kamikochi) |
| `11` | 上高地/復路中房・蝶ヶ岳温泉発 (Kamikochi / Return via Nakabusa) |
| `12` | 上高地/復路新穂高発 (Kamikochi / Return via Shinhotaka) |
| `13` | 新穂高温泉 (Shinhotaka Onsen) |
| `14` | 新穂高温泉/復路上高地発 (Shinhotaka Onsen / Return via Kamikochi) |
| `15` | 新穂高温泉/復路折立発 (Shinhotaka Onsen / Return via Oritate) |
| `16` | 新穂高温泉/復路七倉発 (Shinhotaka Onsen / Return via Nanakura) |
| `17` | 乗鞍岳 (Mt. Norikura) |
| `18` | 立山（室堂） (Tateyama Murodo) |
| `19` | 立山（室堂）/復路折立発 (Tateyama Murodo / Return via Oritate) |
| `20` | 立山（室堂）/復路栂池・八方・五竜・大町発 (Tateyama Murodo / Return via Tsugaike/Happo) |
| `21` | 薬師・黒部（折立） (Yakushi / Kurobe / Oritate) |
| `22` | 薬師・黒部（折立）/復路室堂発 (Yakushi / Kurobe / Return via Murodo) |
| `23` | 薬師・黒部（折立）/復路新穂高発 (Yakushi / Kurobe / Return via Shinhotaka) |
| `24` | 白馬猿倉 (Hakuba Sarukura) |
| `25` | 白馬猿倉/復路栂池・八方・五竜・大町発 (Hakuba Sarukura / Return via Tsugaike/Happo) |
| `26` | 白馬八方・栂池・扇沢・七倉 (Hakuba Happo / Tsugaike / Ogizawa / Nanakura) |
| `27` | 裏銀座（七倉）/復路新穂高発 (Ura-Ginza Nanakura / Return via Shinhotaka) |
| `28` | 燕岳・常念岳 (Mt. Tsubakuro / Mt. Jonen) |
| `29` | 燕岳・常念岳/復路上高地発 (Mt. Tsubakuro / Return via Kamikochi) |
| `30` | 蝶ヶ岳（三股） (Mt. Chogatake / Mimata) |
| `31` | 蝶ヶ岳（三股）/復路上高地発 (Mt. Chogatake / Return via Kamikochi) |
| `32` | 八ヶ岳（深夜着・朝着） (Yatsugatake) |
| `33` | 甲斐駒（黒戸尾根）・甲府駅南口 (Kaikoma Kuroto / Kofu Station) |
| `34` | 甲武信ヶ岳・金峰山 (Mt. Kobushi / Mt. Kinpu) |
| `35` | 谷川岳（ロープウェイ駅） (Mt. Tanigawa Ropeway) |
| `36` | 苗場山 (Mt. Naeba) |
| `37` | 平標山 (Mt. Taira-happyo) |
| `38` | 早池峰山・栗駒山 (Mt. Hayachine / Mt. Kurikoma) |
| `39` | 安達太良山・磐梯山 (Mt. Adatara / Mt. Bandai) |
| `40` | 会津駒ヶ岳・尾瀬御池・燧ヶ岳 (Aizu-Komagatake / Oze Miike / Hiuchigatake) |
| `41` | 月山・鳥海山 (Mt. Gassan / Mt. Chokai) |
| `42` | 日光白根山・男体山 (Nikko Shirane / Mt. Nantai) |

---

## 3. Tour Style (`style` / スタイル)

Query parameter: `style={id}`

| Query ID | Style Name (Japanese) | English Description |
| :---: | :--- | :--- |
| `1` | バスのみ往復 | Round-trip bus only |
| `2` | バスのみ往路 | Outbound bus only |
| `3` | バスのみ復路 | Inbound bus only |
| `4` | 山小屋付き往復 | Round-trip bus with mountain lodge lodging |
| `5` | 山小屋付き往路 | Outbound bus with mountain lodge lodging |
| `6` | 夜行日帰り/往復夜行 | Overnight day-trip / Round-trip overnight bus |
| `7` | タクシープラン | Taxi plan |

---

## 4. Return Date (`return_day` / 復路乗車日)

Query parameter: `return_day={id}`

| Query ID | Option Name | Time Description |
| :---: | :--- | :--- |
| `1` | 出発の1日後（夜行日帰り/往復夜行） | 1 day after departure (Overnight day-trip) |
| `2` | 出発の2日後（現地1泊） | 2 days after departure (1 night stay) |
| `3` | 出発の3日後（現地2泊） | 3 days after departure (2 nights stay) |
| `4` | 出発の4日後（現地3泊） | 4 days after departure (3 nights stay) |
| `5` | 出発の5日後（現地4泊） | 5 days after departure (4 nights stay) |

---

## 5. Bus Seat (`bus_sheet` / バスシート)

Query parameter: `bus_sheet={id}`

| Query ID | Bus Seat Type |
| :---: | :--- |
| `1` | スタンダード (Standard seat) |
| `2` | プレミアム (Premium seat) |
| `3` | 往プレミアム、復スタンダード (Outbound Premium, Inbound Standard) |
| `4` | 往スタンダード、復プレミアム (Outbound Standard, Inbound Premium) |
| `5` | ダブルシート (Double seat option) |
| `6` | タクシー (Taxi option) |

---

## 6. Mountain Lodges (`stay1`, `stay2`, `stay3` / 現地1/2/3泊目の山小屋)

Query parameter: `stay1={id}`, `stay2={id}`, `stay3={id}`

| Query ID | Mountain Lodge Name (山小屋) |
| :---: | :--- |
| `1` | 西穂山荘RW券付 (Nishiho Sanso with Ropeway ticket) |
| `2` | 西穂山荘 (Nishiho Sanso) |
| `3` | 涸沢小屋 (Karasawa Koya) |
| `4` | 蝶ヶ岳ヒュッテ (Chogatake Hutte) |
| `5` | 燕山荘 (Enzanso) |
| `6` | 大天荘 (Daitenso) |
| `7` | 常念小屋 (Jonen Koya) |
| `8` | ヒュッテ大槍 / 大滝山荘 (Hutte OYari / Otaki Sanso) |
| `9` | ヒュッテ西岳 (Hutte Nishidake) |
| `11` | 白馬・五竜・扇沢地区山小屋 (Hakuba/Goryu/Ogizawa Lodges) |
| `12` | 太郎平グループ山小屋 (Taro-daira Group Lodges) |
| `14` | 雷鳥沢ヒュッテ（個室） (Raichozawa Hutte - Private Room) |
| `15` | 雷鳥沢ヒュッテ（相部屋） (Raichozawa Hutte - Shared Room) |
| `16` | 立山一ノ越山荘 (Tateyama Ichinokoshi Sanso) |
| `17` | 雷鳥荘（相部屋） (Raichoso - Shared Room) |
| `18` | 雷鳥荘（個室） (Raichoso - Private Room) |
| `19` | 赤岳天望荘（相部屋） (Akadake Temposo - Shared Room) |
| `20` | 赤岳天望荘（大部屋） (Akadake Temposo - Large Dorm) |
| `21` | 赤岳天望荘（2-3名個室） (Akadake Temposo - 2-3p Private) |
| `22` | 八ヶ岳地区山小屋 (Yatsugatake Region Lodges) |
| `23` | お客様手配 (Self-arranged by customer) |
| `24` | 笠ヶ岳山荘 (Kasagatake Sanso) |
| `25` | 中房温泉ロッジ (Nakabusa Onsen Lodge) |

---

## 7. Search & Filter Parameters Summary

Full query string structure for API and Web requests:

```text
https://api.bus.maitabi.jp/tour_search?departure={1|2|3}&month={1..12}&day={1..31}&area={0..42}&style={1..7}&return_day={1..5}&bus_sheet={1..6}&stay1={id}&stay2={id}&stay3={id}&page={1..N}&travel_type=3
```
