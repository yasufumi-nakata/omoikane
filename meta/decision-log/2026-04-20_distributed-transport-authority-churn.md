# Context

- distributed transport reference runtime は live root directory と bounded authority-plane fleet までは machine-checkable でしたが、
  key-server fleet が入れ替わる過程の continuity contract が未固定でした。
- `specs/schemas/README.md` には dynamic remote key-server churn handling が future work として残っていました。

# Decision

authority-plane churn を `distributed_transport_authority_churn_window` として reference runtime 化します。

- previous / next authority-plane snapshot は `council_tier` / `transport_profile` /
  `directory_digest` / `key_epoch` / `quorum_requirement` を維持しなければなりません。
- churn がある場合は retained server ref を少なくとも 1 つ要求します。
- disappear する key server は previous snapshot で `draining` 済みでなければ fail-closed にします。
- next snapshot の `trusted_root_refs` は引き続き `trust_root_quorum` を満たす必要があります。

# Consequences

- `distributed-transport-demo` は initial authority plane と churned authority plane を両方出し、
  `authority_churn` で overlap / draining exit / quorum continuity を確認できます。
- schema / IDL / eval / docs が同じ churn contract を参照できるため、
  hourly builder が distributed transport surface を再利用しやすくなります。
- future work は `actual non-loopback mTLS authority routing` と socket-level tracing へ縮小されます。
