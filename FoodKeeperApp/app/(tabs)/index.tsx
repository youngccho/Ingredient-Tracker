import React, { useState } from 'react'
import { 
  StyleSheet, 
  TextInput, 
  Button, 
  FlatList, 
  View 
} from 'react-native'
import { Image } from 'expo-image'

import ParallaxScrollView from '@/components/ParallaxScrollView'
import { ThemedText } from '@/components/ThemedText'
import { ThemedView } from '@/components/ThemedView'

export default function HomeScreen() {
  // ─── state for lookup ───────────────────────────────────────
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)

  // ─── lookup function ────────────────────────────────────────
  const lookup = async () => {
    setError(null)
    try {
      // adjust this if you run on Android emulator (10.0.2.2)
      const base = 'http://192.168.12.129:5001'
      const resp = await fetch(`${base}/lookup?query=${encodeURIComponent(query)}`)
      if (!resp.ok) {
        const { message } = await resp.json().catch(() => ({}))
        throw new Error(message || 'No matches')
      }
      const { matches } = await resp.json()
      setResults(matches)
    } catch (e: any) {
      setResults([])
      setError(e.message)
    }
  }

  return (
    <ParallaxScrollView
      headerBackgroundColor={{ light: '#A1CEDC', dark: '#1D3D47' }}
      headerImage={
        <Image
          source={require('@/assets/images/partial-react-logo.png')}
          style={styles.reactLogo}
        />
      }>

      {/* ———————————————————————————————————————————————
             Your existing welcome UI
      ——————————————————————————————————————————————— */}
      <ThemedView style={styles.titleContainer}>
        <ThemedText type="title">Welcome!</ThemedText>
      </ThemedView>

      {/* ———————————————————————————————————————————————
             NEW: Lookup UI
      ——————————————————————————————————————————————— */}
      <ThemedView style={styles.lookupContainer}>
        <ThemedText type="subtitle">Lookup Ingredient</ThemedText>

        <TextInput
          style={styles.input}
          placeholder="eg. milk, bread, cheese…"
          value={query}
          onChangeText={setQuery}
        />
        <Button title="Lookup" onPress={lookup} />

        {error && (
          <ThemedText type="default" style={styles.error}>
            {error}
          </ThemedText>
        )}

        <FlatList
          data={results}
          keyExtractor={(_, i) => i.toString()}
          renderItem={({ item }) => (
            <View style={styles.card}>
              <ThemedText type="defaultSemiBold">{item.name}</ThemedText>
              {item.shelf_life.map((e: any, idx: number) => (
                <ThemedText key={idx} type="default">
                  • {e.storage} ({e.context}): {e.min_days}–{e.max_days}d
                </ThemedText>
              ))}
            </View>
          )}
        />
      </ThemedView>

      {/* ———————————————————————————————————————————————
             (Optional) keep your old steps or other tabs below
      ——————————————————————————————————————————————— */}
      <ThemedView style={styles.stepContainer}>
        <ThemedText type="subtitle">Step 2: Explore</ThemedText>
        <ThemedText>
          Tap the Explore tab to learn more about this starter app.
        </ThemedText>
      </ThemedView>

    </ParallaxScrollView>
  )
}

const styles = StyleSheet.create({
  titleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 16,
  },
  lookupContainer: {
    marginBottom: 24,
    paddingHorizontal: 16,
  },
  input: {
    height: 40,
    borderWidth: 1,
    borderColor: '#999',
    paddingHorizontal: 8,
    marginVertical: 8,
    borderRadius: 4,
  },
  error: {
    color: 'red',
    marginBottom: 8,
  },
  card: {
    padding: 12,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 6,
    marginVertical: 6,
  },
  stepContainer: {
    gap: 8,
    marginBottom: 8,
    paddingHorizontal: 16,
  },
  reactLogo: {
    height: 178,
    width: 290,
    bottom: 0,
    left: 0,
    position: 'absolute',
  },
})
