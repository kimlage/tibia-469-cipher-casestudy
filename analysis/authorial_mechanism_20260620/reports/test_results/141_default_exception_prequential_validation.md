# 141. Default/Exception Prequential Validation

Classification: `default_exception_components_online_predictive_frozen_unstable`
Translation delta: `NONE`

## Purpose

Audits 136 and 137 promoted copy-length and copy-source
default/exception ledgers. This audit asks whether those components
predict held-out books with frozen train counts, or whether the gains
are only full-corpus compression. It does not search new parameters.

## Prefix Future-Suffix Splits

| Split | Train books | Test books | Online gain | Frozen gain | Copy-length online | Copy-source online |
|---|---:|---:|---:|---:|---:|---:|
| `prefix_10_future_suffix` | `10` | `60` | `208.095` | `-39.773` | `171.441` | `36.654` |
| `prefix_20_future_suffix` | `20` | `50` | `168.965` | `6.277` | `137.011` | `31.953` |
| `prefix_35_future_suffix` | `35` | `35` | `129.591` | `49.413` | `101.760` | `27.832` |
| `prefix_50_future_suffix` | `50` | `20` | `62.988` | `24.245` | `60.002` | `2.986` |
| `prefix_60_future_suffix` | `60` | `10` | `43.582` | `34.276` | `37.679` | `5.903` |

## Summary

- Prefix online gain summary: `{'n': 5, 'min': 43.58194815526494, 'median': 129.5911877640342, 'mean': 122.64421074460358, 'max': 208.09508014545872}`
- Prefix frozen gain summary: `{'n': 5, 'min': -39.77278285456532, 'median': 24.244748602373306, 'mean': 14.88759527531775, 'max': 49.41302642639016}`
- Block online gain summary: `{'n': 7, 'min': 14.355300481104905, 'median': 18.569623593433107, 'mean': 24.466169607776095, 'max': 44.554309330633714}`
- Family online gain summary: `{'n': 19, 'min': -10.257664615486505, 'median': 2.7278809377826008, 'mean': 4.018434446881475, 'max': 24.80574124781078}`
- Family nonpositive failures: `[{'label': 'hellgate_public_bookcase_1', 'online_gain_vs_uniform_bits': -7.590397851586403, 'frozen_gain_vs_uniform_bits': -23.067716822618635, 'component_gain_vs_uniform_bits': {'copy_length_online': -3.8572007416978593, 'copy_length_frozen': -11.0753584190387, 'copy_source_online': -3.7331971098885504, 'copy_source_frozen': -11.992358403579942}}, {'label': 'hellgate_public_bookcase_10', 'online_gain_vs_uniform_bits': 6.194741678595577, 'frozen_gain_vs_uniform_bits': -24.565596492655345, 'component_gain_vs_uniform_bits': {'copy_length_online': 9.331718762657715, 'copy_length_frozen': -11.680201132714295, 'copy_source_online': -3.1369770840621385, 'copy_source_frozen': -12.885395359941043}}, {'label': 'hellgate_public_bookcase_12', 'online_gain_vs_uniform_bits': -5.357200715714342, 'frozen_gain_vs_uniform_bits': -23.377062550772322, 'component_gain_vs_uniform_bits': {'copy_length_online': -1.2733294260576145, 'copy_length_frozen': -9.414290821056937, 'copy_source_online': -4.083871289656727, 'copy_source_frozen': -13.962771729715385}}, {'label': 'hellgate_public_bookcase_2', 'online_gain_vs_uniform_bits': -2.5400376427694766, 'frozen_gain_vs_uniform_bits': -19.497148119391227, 'component_gain_vs_uniform_bits': {'copy_length_online': 1.5073658492744073, 'copy_length_frozen': -4.505288018581652, 'copy_source_online': -4.047403492043884, 'copy_source_frozen': -14.991860100809589}}, {'label': 'hellgate_public_bookcase_22', 'online_gain_vs_uniform_bits': -6.089639222881601, 'frozen_gain_vs_uniform_bits': -33.28626915208304, 'component_gain_vs_uniform_bits': {'copy_length_online': -1.2940262236328124, 'copy_length_frozen': -11.318703660066717, 'copy_source_online': -4.795612999248817, 'copy_source_frozen': -21.967565492016348}}, {'label': 'hellgate_public_bookcase_23', 'online_gain_vs_uniform_bits': -5.661011365323461, 'frozen_gain_vs_uniform_bits': -11.321209108811843, 'component_gain_vs_uniform_bits': {'copy_length_online': -2.3305584881770685, 'copy_length_frozen': -2.324102589718038, 'copy_source_online': -3.3304528771463993, 'copy_source_frozen': -8.997106519093819}}, {'label': 'hellgate_public_bookcase_3', 'online_gain_vs_uniform_bits': -0.3783962090823252, 'frozen_gain_vs_uniform_bits': -12.421786552526271, 'component_gain_vs_uniform_bits': {'copy_length_online': 3.09577249182, 'copy_length_frozen': -2.4260459939271044, 'copy_source_online': -3.474168700902325, 'copy_source_frozen': -9.995740558599167}}, {'label': 'hellgate_public_bookcase_36', 'online_gain_vs_uniform_bits': -10.257664615486505, 'frozen_gain_vs_uniform_bits': -14.822139456177695, 'component_gain_vs_uniform_bits': {'copy_length_online': -7.069033164705004, 'copy_length_frozen': -6.830342039131644, 'copy_source_online': -3.1886314507815, 'copy_source_frozen': -7.991797417046058}}, {'label': 'hellgate_public_bookcase_4', 'online_gain_vs_uniform_bits': 2.7278809377826008, 'frozen_gain_vs_uniform_bits': -1.0118030440398371, 'component_gain_vs_uniform_bits': {'copy_length_online': 5.904910627702293, 'copy_length_frozen': 6.985313731128663, 'copy_source_online': -3.177029689919692, 'copy_source_frozen': -7.997116775168507}}, {'label': 'hellgate_public_bookcase_6', 'online_gain_vs_uniform_bits': -0.5400704231845666, 'frozen_gain_vs_uniform_bits': -1.3098417758446672, 'component_gain_vs_uniform_bits': {'copy_length_online': 1.782321867109319, 'copy_length_frozen': 2.689212462717837, 'copy_source_online': -2.322392290293891, 'copy_source_frozen': -3.9990542385625076}}, {'label': 'hellgate_public_bookcase_7', 'online_gain_vs_uniform_bits': -8.751425580878447, 'frozen_gain_vs_uniform_bits': -21.587102327618993, 'component_gain_vs_uniform_bits': {'copy_length_online': -4.832232017704428, 'copy_length_frozen': -7.589395996967355, 'copy_source_online': -3.9191935631740478, 'copy_source_frozen': -13.997706330651681}}]`

## Decision

The default/exception components retain positive online gains on all prefix holdouts, but frozen counts from the first 10 books lose to the legal uniform baseline because copy-source prediction is sparse. The components are therefore online-predictive but not stable enough to promote as a frozen generation method.

## Boundary

- No compression-bound change is introduced here.
- No plaintext or translation is introduced.
- Row0/table origin is unchanged.
